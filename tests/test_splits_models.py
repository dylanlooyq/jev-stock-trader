"""Walk-forward boundaries, the holdout lock, preprocessing isolation and model behaviour."""
import numpy as np
import pandas as pd
import pytest

from jevbench import BUY, HOLD, SELL
from jevbench.benchmark import walk_forward
from jevbench.config import deep_update, embargo_days, load_config
from jevbench.data import lock_holdout
from jevbench.dataset import build_dataset
from jevbench.features import FEATURES
from jevbench.models import make_models
from jevbench.models.classical import LogReg, StratifiedRandom
from jevbench.models.rules import MomentumRule, MovingAverageCrossRule
from jevbench.splits import assert_holdout_locked, fold_frames, make_folds


@pytest.fixture()
def ds(cfg, prices):
    return build_dataset(prices, cfg)


def test_folds_are_chronological_and_purged(cfg, ds):
    dates = pd.DatetimeIndex(sorted(ds["date"].unique()))
    for h in cfg["task"]["horizons"]:
        folds = make_folds(ds["date"], cfg, h)
        assert len(folds) >= 3
        gap = h + 1 + embargo_days(cfg, h)
        for fold in folds:
            f = fold_frames(ds, fold, h)
            assert f["train"]["date"].max() < f["val"]["date"].min() < f["test"]["date"].min()
            assert f["val"]["date"].max() < f["test"]["date"].min()
            # No fitted row's label may depend on prices from the next segment.
            assert f["train"][f"label_end_{h}"].max() < fold.val_start
            assert f["val"][f"label_end_{h}"].max() < fold.test_start
            assert f["trainval"][f"label_end_{h}"].max() < fold.test_start
            # At least `gap` trading days separate the last fitted date from the first test date.
            last_fit = dates.get_loc(f["trainval"]["date"].max())
            first_test = dates.get_loc(f["test"]["date"].min())
            assert first_test - last_fit > gap - 1
            assert set(f["trainval"]["date"]).isdisjoint(f["test"]["date"])


def test_test_folds_do_not_overlap(cfg, ds):
    folds = make_folds(ds["date"], cfg, 5)
    for a, b in zip(folds, folds[1:]):
        assert a.test_end <= b.test_start
        assert b.train_end >= a.train_end   # expanding window


def test_holdout_flag_and_boundary_validation(cfg, ds):
    folds = make_folds(ds["date"], cfg, 5)
    holdout_start = pd.Timestamp(cfg["splits"]["holdout_start"])
    assert [f.is_holdout for f in folds] == [f.test_start >= holdout_start for f in folds]
    assert any(f.is_holdout for f in folds) and not all(f.is_holdout for f in folds)
    bad = deep_update(cfg, {"splits": {"holdout_start": "2021-08-15"}})
    with pytest.raises(ValueError, match="fold boundary"):
        make_folds(ds["date"], bad, 5)


def test_locked_run_never_sees_holdout_data(cfg, prices, ds):
    holdout_start = pd.Timestamp(cfg["splits"]["holdout_start"])
    locked = build_dataset(lock_holdout(prices, cfg), cfg)
    assert locked["date"].max() < holdout_start
    for h in cfg["task"]["horizons"]:
        assert locked[f"label_end_{h}"].dropna().max() < holdout_start
    assert_holdout_locked(locked, make_folds(locked["date"], cfg, 5), cfg)
    with pytest.raises(RuntimeError, match="Holdout"):
        assert_holdout_locked(ds, make_folds(ds["date"], cfg, 5), cfg)


def test_locked_features_equal_unlocked_features_before_the_holdout(cfg, prices, ds):
    """Locking the holdout must not change any development row."""
    locked = build_dataset(lock_holdout(prices, cfg), cfg)
    merged = locked[["date", "ticker", *FEATURES]].merge(
        ds[["date", "ticker", *FEATURES]], on=["date", "ticker"], suffixes=("", "_full"))
    assert len(merged) == len(locked)
    for col in FEATURES:
        np.testing.assert_array_equal(merged[col].to_numpy(), merged[f"{col}_full"].to_numpy())


def test_alias_model_ids_are_rejected():
    with pytest.raises(ValueError, match="pinned"):
        load_config(overrides=[{"jev": {"model": "jev-latest"}}])


def test_scaler_is_fitted_on_fitting_rows_only(cfg, ds):
    fold = make_folds(ds["date"], cfg, 5)[0]
    frames = fold_frames(ds, fold, 5)
    model = LogReg("logreg", cfg["models"]["logreg"], FEATURES, 1)
    model.fit({k: frames[k] for k in ("train", "val", "trainval")}, "label_5", seed=1)   # no test frame at all
    scaler = model.estimator_.named_steps["standardscaler"]
    np.testing.assert_allclose(scaler.mean_, frames["trainval"][FEATURES].mean().to_numpy(), rtol=1e-9)
    assert not np.allclose(scaler.mean_, ds[FEATURES].mean().to_numpy(), rtol=1e-6)


def test_models_never_read_the_test_frame_during_fit(cfg, ds):
    class NoTest(dict):
        def __getitem__(self, key):
            if key == "test":
                raise AssertionError("fit() accessed the test frame")
            return super().__getitem__(key)

    fold = make_folds(ds["date"], cfg, 5)[0]
    frames = fold_frames(ds, fold, 5)
    guarded = NoTest({k: v for k, v in frames.items() if k != "test"})
    cfg = deep_update(cfg, {"models": {"enabled": [
        "majority", "stratified_random", "logreg", "random_forest", "gbt", "momentum_rule", "ma_cross_rule"]}})
    for model in make_models(cfg):
        info = model.fit(guarded, "label_5", seed=3)
        assert 0.0 <= info["val_macro_f1"] <= 1.0
        pred, proba = model.predict(frames["test"])
        assert set(np.unique(pred)) <= {SELL, HOLD, BUY}
        if model.has_proba:
            np.testing.assert_allclose(proba.sum(axis=1), 1.0, atol=1e-9)
        else:
            assert proba is None


def test_every_model_gets_the_same_tuning_budget():
    cfg = load_config()
    sizes = {name: len(cfg["models"][name]["grid"]) for name in ("logreg", "random_forest", "gbt")}
    assert len(set(sizes.values())) == 1, sizes


def test_stratified_random_is_reproducible(cfg, ds):
    frames = fold_frames(ds, make_folds(ds["date"], cfg, 5)[0], 5)
    runs = []
    for _ in range(2):
        model = StratifiedRandom()
        model.fit(frames, "label_5", seed=11)
        runs.append(model.predict(frames["test"])[0])
    np.testing.assert_array_equal(runs[0], runs[1])


def test_momentum_rule_signals():
    df = pd.DataFrame({"ret_20": [0.20, -0.20, 0.001], "vol_60": [0.01, 0.01, 0.01]})
    rule = MomentumRule("momentum_rule", {"grid": []})
    np.testing.assert_array_equal(rule.signal(df, {"lookback": 20, "band": 0.5}), [BUY, SELL, HOLD])
    np.testing.assert_array_equal(rule.signal(df, {"lookback": 20, "band": 0.0}), [BUY, SELL, BUY])


def test_ma_cross_rule_matches_moving_average_definition():
    close, sma_fast, sma_slow = 100.0, np.array([95.0, 105.0, 95.0]), np.array([90.0, 110.0, 99.0])
    df = pd.DataFrame({"dist_sma_20": close / sma_fast - 1, "dist_sma_50": close / sma_slow - 1})
    rule = MovingAverageCrossRule("ma_cross_rule", {"grid": []})
    # fast above slow -> BUY; fast below slow -> SELL (rows 1 and 2).
    np.testing.assert_array_equal(rule.signal(df, {"fast": 20, "slow": 50, "confirm": False}), [BUY, SELL, SELL])
    # With confirmation, row 2 (price above the fast average while fast < slow) becomes HOLD.
    np.testing.assert_array_equal(rule.signal(df, {"fast": 20, "slow": 50, "confirm": True}), [BUY, SELL, HOLD])


def test_walk_forward_scores_all_models_on_identical_rows(cfg, prices):
    run = walk_forward(prices, cfg, log=lambda *_: None)
    preds = run["predictions"]
    assert set(preds["segment"]) == {"dev"}
    assert preds["date"].max() < pd.Timestamp(cfg["splits"]["holdout_start"])
    for _, grp in preds.groupby("horizon"):
        keys = {m: set(zip(g["date"], g["ticker"])) for m, g in grp.groupby("model")}
        first = next(iter(keys.values()))
        assert all(k == first for k in keys.values())
        assert not grp.duplicated(["model", "date", "ticker"]).any()
    # Without saved Jev outputs the Jev arms are recorded as not run, never substituted.
    not_run = run["fit_log"][run["fit_log"]["status"] != "ok"]
    assert set(not_run["family"]) == {"jev"}
    assert not preds["model"].str.startswith("jev").any()


ROLLING = {"splits": {"train_window_months": 6, "validation_months": 2, "test_months": 6, "min_train_days": 20}}


def test_rolling_window_bounds_the_training_rows_and_keeps_the_purge(cfg, ds):
    rolling = deep_update(cfg, ROLLING)
    dates = pd.DatetimeIndex(sorted(ds["date"].unique()))
    folds = make_folds(ds["date"], rolling, 5)
    expanding = make_folds(ds["date"], cfg, 5)
    assert len(folds) >= 2 and all(f.train_start is not None for f in folds)
    assert all(f.train_start is None for f in expanding)
    gap = 5 + 1 + embargo_days(rolling, 5)
    for fold in folds:
        f = fold_frames(ds, fold, 5)
        assert f["train"]["date"].min() >= fold.train_start
        assert f["trainval"]["date"].min() >= fold.train_start
        # the window is about six months of trading days, not everything before the fold
        assert dates.get_loc(f["train"]["date"].max()) - dates.get_loc(f["train"]["date"].min()) < 135
        assert f["train"]["date"].max() < f["val"]["date"].min() < f["test"]["date"].min()
        assert f["trainval"][f"label_end_5"].max() < fold.test_start
        last_fit = dates.get_loc(f["trainval"]["date"].max())
        assert dates.get_loc(f["test"]["date"].min()) - last_fit > gap - 1
        assert set(f["trainval"]["date"]).isdisjoint(f["test"]["date"])
    # same test blocks as the expanding design, so the two are comparable
    assert [f.test_start for f in folds] == [f.test_start for f in expanding][: len(folds)]


def test_rolling_window_drops_old_history_that_expanding_keeps(cfg, ds):
    rolling = deep_update(cfg, ROLLING)
    last_rolling = fold_frames(ds, make_folds(ds["date"], rolling, 5)[-1], 5)
    last_expanding = fold_frames(ds, make_folds(ds["date"], cfg, 5)[-1], 5)
    assert last_rolling["train"]["date"].min() > last_expanding["train"]["date"].min()
    assert len(last_rolling["train"]) < len(last_expanding["train"])


def test_rolling_folds_with_too_short_a_validation_window_are_skipped(cfg, ds):
    rolling = deep_update(cfg, ROLLING)
    assert make_folds(ds["date"], rolling, 5)
    strict = deep_update(rolling, {"splits": {"min_val_days": 40}})
    assert make_folds(ds["date"], strict, 5) == []
