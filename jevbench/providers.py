"""External decision models: classifiers we query instead of train.

Every provider answers the same questions about the same anonymised state, and its
answers are saved as columns with the provider's prefix. The benchmark then builds the
same three arms for each provider:

  <provider>_signal_<variant>            the provider's own probabilities, used directly
  <provider>_head_<variant>              a gradient-boosted model trained on its outputs
  <provider>_plus_controlled_<variant>   the same model on controlled features + its outputs

Variants: "zero" (no worked examples) and "examples" (training examples in the request).

Adding a provider means writing one module that produces its output table and manifest
(see jev.annotate and jev.attach_outputs), registering it here, and enabling its arms
in config `models.enabled`. Nothing else in the benchmark changes. Each provider is a
separate research question with its own multiple-comparison family; record it in
EXPERIMENT_MEMORY.md before running it.
"""
from __future__ import annotations

VARIANTS = ("zero", "examples")

PROVIDERS = {
    "jev": {
        "label": "Jev (TypeSafe jev-1.13.0)",
        "prefix": {"zero": "jevz", "examples": "jevx"},
        "implemented": True,     # client and annotator exist; never run against the live API
    },
    "openai": {
        "label": "OpenAI classifier",
        "prefix": {"zero": "oaiz", "examples": "oaix"},
        "implemented": False,    # reserved: no client yet
    },
    "local": {
        "label": "Local open model (option logits)",
        "prefix": {"zero": "lclz", "examples": "lclx"},
        "implemented": False,    # reserved: no client yet
    },
}

ARM_KINDS = {
    "signal": "{label} as signal",
    "head": "GBT on {label} outputs",
    "plus_controlled": "GBT on controlled features + {label} outputs",
}


def prefix(provider: str, variant: str) -> str:
    return PROVIDERS[provider]["prefix"][variant]


def arm_name(provider: str, kind: str, variant: str) -> str:
    return f"{provider}_{kind}_{variant}"


def describe_arm(name: str) -> str:
    for provider, spec in PROVIDERS.items():
        for kind, template in ARM_KINDS.items():
            for variant in VARIANTS:
                if name == arm_name(provider, kind, variant):
                    suffix = "zero-shot" if variant == "zero" else "with training examples"
                    return f"{template.format(label=spec['label'])}, {suffix}"
    return name
