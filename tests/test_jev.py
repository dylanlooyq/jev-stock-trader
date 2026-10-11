"""Jev integration, exercised against a mock transport. Nothing here touches the network."""
import json
import re

import numpy as np
import pandas as pd
import pytest

from jevbench import NO_PREDICTION, jev
from jevbench.benchmark import walk_forward
from jevbench.config import deep_update
from jevbench.data import lock_holdout
from jevbench.dataset import build_dataset
from jevbench.features import FEATURES
from jevbench.models.jev_arms import JevSignal

from .conftest import TICKERS


@pytest.fixture()
def ctx(cfg, prices):
    return jev.JevContext(build_dataset(prices, cfg, keep_burn_in=True), cfg)


def mock_transport(model="jev-1.13.0", calls=None, fail_first=0, status=200):
    """A fake API: valid answers whose probabilities depend on the option order sent."""
    state = {"n": 0}

    def send(payload):
        state["n"] += 1
        if calls is not None:
            calls.append(payload)
        if state["n"] <= fail_first:
            return 429, {"error": "rate limited"}, {"retry-after": "0"}
        if status != 200:
            return status, {"error": "bad request"}, {}
        answers = {}
        for qid, q in payload["questions"].items():
            if q["type"] == "choice":
                options = list(q["criteria"])
                probs = dict(zip(options, [0.5, 0.3, 0.2]))      # leans to the first-listed option
                answers[qid] = {"type": "choice", "choice": options[0], "probabilities": probs, "confidence": 0.25}
            else:
                answers[qid] = {"type": "noul", "noul": 0.6}
        return 200, {"model": model, "answers": answers, "usage": {"input_tokens": 1000, "output_tokens": 10}}, {}

    return send


def client_for(cfg, transport, budget=1.0):
    return jev.JevClient(cfg, approved_cost_usd=budget, transport=transport, cache_path=":memory:",
                         sleep=lambda _s: None, rate_limited=False)


def test_rate_limiter_spaces_requests():
    limiter = jev.RateLimiter(requests_per_s=100, tokens_per_s=1e9, safety=1.0)
    started = jev.time.monotonic()
    for _ in range(11):
        limiter.wait(tokens=1)
    assert jev.time.monotonic() - started >= 0.09      # 10 intervals of 10 ms


# ----------------------------------------------------------------- state construction

def test_state_reveals_no_ticker_date_or_price_level(ctx, cfg):
    for i in (len(ctx.full) // 2, len(ctx.full) - 1):
        for with_examples in (False, True):
            text = json.dumps(ctx.state(i, with_examples))
            assert not any(t in text for t in TICKERS)
            assert not re.search(r"\b(19|20)\d{2}\b", text), "a calendar year leaked into the state"
            assert "date" not in text.lower().replace("update", "")
            assert not re.search(r"\$\s?\d", text)
    snapshot = ctx.state(len(ctx.full) - 1, False)["snapshot"]
    assert len(snapshot["stock"]) + len(snapshot["market"]) == len(FEATURES)
    assert all(v.split(" (")[0] in jev.BUCKET_LABELS for group in snapshot.values() for v in group.values())


def test_cutpoints_use_only_dates_before_the_month(ctx, cfg, prices):
    month = pd.Period("2020-09", "M")
    base = ctx.cutpoints(month).copy()
    full = ctx.full.copy()
    full.loc[full["date"] >= month.to_timestamp(), FEATURES] *= 10.0     # corrupt the month and everything after
    np.testing.assert_array_equal(jev.JevContext(full, cfg).cutpoints(month), base)
    assert base.shape == (len(FEATURES), len(cfg["jev"]["bucket_quantiles"]))
    assert (np.diff(base, axis=1) >= 0).all()


def test_examples_come_only_from_settled_history(ctx, cfg):
    for month in (pd.Period("2020-03", "M"), pd.Period("2021-11", "M")):
        month_start = ctx.dates[ctx.month_start_pos(month)]
        pool = ctx.example_rows(month)
        assert len(pool) > 0
        assert pool["date"].max() < month_start
        for h in cfg["task"]["horizons"]:
            assert pool[f"label_end_{h}"].max() < month_start
        cases = ctx.examples(month)
        assert len(cases) == 3 * cfg["jev"]["examples_per_class"]
        assert ctx.examples(month) is cases                         # same set for every row in the month


def test_state_is_identical_whether_or_not_future_data_exists(ctx, cfg, prices):
    """A row's state must not depend on later data, so it is the same in every fold."""
    cutoff = pd.Timestamp("2020-12-31")
    early = jev.JevContext(build_dataset(prices[prices["date"] <= cutoff], cfg, keep_burn_in=True), cfg)
    row_date = pd.Timestamp("2020-10-15")
    i_full = ctx.full.index[(ctx.full["date"] == row_date) & (ctx.full["ticker"] == "CCC")][0]
    i_early = early.full.index[(early.full["date"] == row_date) & (early.full["ticker"] == "CCC")][0]
    for with_examples in (False, True):
        assert ctx.state(i_full, with_examples) == early.state(i_early, with_examples)


def test_questions_cover_each_horizon_with_rotated_option_orders(cfg):
    questions = jev.build_questions(cfg)
    assert len(questions) == 5 * len(cfg["task"]["horizons"])
    orders = [tuple(questions[f"h5_signal_o{i}"]["criteria"]) for i in range(3)]
    assert len(set(orders)) == 3 and {o[0] for o in orders} == {"BUY", "HOLD", "SELL"}
    assert "0.5 times its typical 5-day move" in questions["h5_signal_o0"]["instructions"]
    assert "0.5 times its typical 5-day move" in questions["h5_big"]["instructions"]
    fixed = deep_update(cfg, {"task": {"label": {"method": "fixed"}}})
    assert "The threshold is 1.5%." in jev.build_questions(fixed)["h5_signal_o0"]["instructions"]
    assert jev.request_fingerprint(fixed) != jev.request_fingerprint(cfg)


# ----------------------------------------------------------------- answer parsing

def _choice(sell, hold, buy):
    return {"type": "choice", "choice": "BUY", "probabilities": {"SELL": sell, "HOLD": hold, "BUY": buy}}


def test_parse_averages_valid_option_orders():
    answers = {"h5_signal_o0": _choice(0.2, 0.3, 0.5), "h5_signal_o1": _choice(0.4, 0.3, 0.3),
               "h5_signal_o2": _choice(0.3, 0.3, 0.4), "h5_up": {"type": "noul", "noul": 0.7},
               "h5_big": {"type": "noul", "noul": 0.2}}
    out = jev.parse_answers(answers, [5])
    assert (out["p_sell_5"], out["p_hold_5"], out["p_buy_5"]) == pytest.approx((0.3, 0.3, 0.4))
    assert out["orders_ok_5"] == 3 and out["order_spread_5"] == pytest.approx(0.2)
    assert out["up_5"] == 0.7 and out["big_5"] == 0.2


def test_parse_rejects_invalid_answers_without_inventing_values():
    answers = {
        "h5_signal_o0": _choice(0.9, 0.9, 0.9),                                  # does not sum to 1
        "h5_signal_o1": {"type": "choice", "probabilities": {"UP": 1.0}},        # wrong labels
        "h5_signal_o2": _choice(0.2, 0.3, float("nan")),                         # not finite
        "h5_up": {"type": "noul", "noul": 1.7},                                  # out of range
    }
    out = jev.parse_answers(answers, [5])
    assert out["orders_ok_5"] == 0
    assert all(np.isnan(out[k]) for k in ("p_sell_5", "p_hold_5", "p_buy_5", "up_5", "big_5"))
    partial = jev.parse_answers({"h5_signal_o1": _choice(0.1, 0.2, 0.7)}, [5])
    assert partial["orders_ok_5"] == 1 and partial["p_buy_5"] == pytest.approx(0.7)


# ----------------------------------------------------------------- client

def test_client_caches_and_tracks_cost(cfg):
    calls = []
    client = client_for(cfg, mock_transport(calls=calls))
    questions = jev.build_questions(cfg)
    first = client.evaluate({"a": 1}, questions)
    again = client.evaluate({"a": 1}, questions)
    assert first == again and len(calls) == 1
    assert client.stats["requests"] == 1 and client.stats["cache_hits"] == 1
    assert client.spent_usd == pytest.approx(1000 * cfg["jev"]["price_usd_per_mtok"] / 1e6)
    assert calls[0]["model"] == "jev-1.13.0"
    client.evaluate({"a": 2}, questions)
    assert len(calls) == 2


def test_client_refuses_an_unpinned_model_answer(cfg):
    client = client_for(cfg, mock_transport(model="jev-1.14.0"))
    with pytest.raises(jev.JevModelMismatch):
        client.evaluate({"a": 1}, jev.build_questions(cfg))


def test_client_stops_before_exceeding_the_approved_budget(cfg):
    calls = []
    client = client_for(cfg, mock_transport(calls=calls), budget=0.0)
    with pytest.raises(jev.JevBudgetExceeded):
        client.evaluate({"a": 1}, jev.build_questions(cfg))
    assert calls == []


def test_client_retries_rate_limits_and_reports_hard_failures(cfg):
    calls = []
    client = client_for(cfg, mock_transport(calls=calls, fail_first=2))
    assert client.evaluate({"a": 1}, jev.build_questions(cfg))["model"] == "jev-1.13.0"
    assert len(calls) == 3

    failing = client_for(cfg, mock_transport(status=400))
    with pytest.raises(jev.JevError):
        failing.evaluate({"a": 1}, jev.build_questions(cfg))
    assert failing.stats["failures"] == 1 and failing.stats["requests"] == 0


def test_client_needs_a_key_for_live_calls(cfg, monkeypatch):
    monkeypatch.setattr(jev, "load_api_key", lambda: None)
    with pytest.raises(jev.JevMissingKey):
        jev.JevClient(cfg, approved_cost_usd=1.0, cache_path=":memory:")


def test_cost_estimate_sends_nothing(ctx, cfg):
    rows = np.arange(len(ctx.full) - 500, len(ctx.full))
    est = jev.estimate_cost(ctx, rows, cfg, n_probe=20)
    assert est["requests_per_variant"] == 500
    assert est["examples"]["approx_tokens_per_request"] > est["zero"]["approx_tokens_per_request"]
    assert est["approx_total_cost_usd"] >= 0


# ----------------------------------------------------------------- end to end with a mock

def _annotate(cfg, prices, variant, transport):
    locked = lock_holdout(prices, cfg)
    ctx = jev.JevContext(build_dataset(locked, cfg, keep_burn_in=True), cfg)
    rows = jev.select_rows(ctx.full, build_dataset(locked, cfg))
    table, manifest = jev.annotate(ctx, rows, variant, client_for(cfg, transport, budget=50.0), cfg, "test-sha")
    parquet_path, manifest_path = jev.outputs_paths(cfg, variant)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(parquet_path, index=False)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return table, manifest, len(rows)


def test_annotate_then_benchmark_runs_the_jev_arms(cfg, prices):
    table, manifest, n_rows = _annotate(cfg, prices, "zero", mock_transport())
    assert len(table) == n_rows == manifest["rows_ok"] and manifest["rows_failed"] == 0
    # Averaging over the three rotated orders removes the mock's first-option lean entirely.
    np.testing.assert_allclose(table[["jevz_p_sell_5", "jevz_p_hold_5", "jevz_p_buy_5"]].to_numpy(), 1 / 3)
    assert table["jevz_order_spread_5"].iloc[0] == pytest.approx(0.3)

    run = walk_forward(prices, cfg, log=lambda *_: None)
    ran = set(run["predictions"]["model"])
    assert {"jev_signal_zero", "jev_head_zero", "jev_plus_controlled_zero"} <= ran
    assert not any(m.endswith("_examples") for m in ran)             # that variant was never annotated
    assert run["jev_status"]["examples"].startswith("not run")
    for _, grp in run["predictions"].groupby("horizon"):
        sizes = grp.groupby("model").size()
        assert sizes.nunique() == 1                                   # identical rows for Jev and baselines


def test_failed_jev_rows_become_no_prediction(cfg, prices):
    table, manifest, _ = _annotate(cfg, prices, "zero", mock_transport(status=400))
    assert manifest["rows_ok"] == 0 and manifest["rows_failed"] == len(table)
    assert table["jevz_status"].str.startswith("error").all()
    ds, status = jev.attach_jev_outputs(build_dataset(lock_holdout(prices, cfg), cfg), cfg)
    model = JevSignal("jev_signal_zero", "zero")
    model.horizon_ = 5
    pred, proba = model.predict(ds.head(50))
    assert (pred == NO_PREDICTION).all() and np.isnan(proba).all()


def test_outputs_from_a_different_configuration_are_refused(cfg, prices):
    _annotate(cfg, prices, "zero", mock_transport())
    ds = build_dataset(lock_holdout(prices, cfg), cfg)
    for changed in ({"task": {"label": {"k": 0.75}}}, {"jev": {"examples_per_class": 2}}):
        merged, status = jev.attach_jev_outputs(ds, deep_update(cfg, changed))
        assert status["zero"].startswith("refused")
        assert "jevz_status" not in merged.columns


def test_partially_annotated_data_does_not_run_as_if_complete(cfg, prices):
    table, manifest, _ = _annotate(cfg, prices, "zero", mock_transport())
    parquet_path, _ = jev.outputs_paths(cfg, "zero")
    table.iloc[: len(table) // 2].to_parquet(parquet_path, index=False)
    run = walk_forward(prices, cfg, log=lambda *_: None)
    assert not run["predictions"]["model"].str.startswith("jev").any()
    reasons = run["fit_log"].loc[run["fit_log"]["family"] == "jev", "status"]
    assert reasons.str.contains("cover only").any()
