"""Benchmark of Jev against traditional classifiers for stock price classification.

Read EXPERIMENT_MEMORY.md at the repository root before changing methodology.
"""

SELL, HOLD, BUY = 0, 1, 2
CLASS_NAMES = ["SELL", "HOLD", "BUY"]
NO_PREDICTION = -1  # a model failed to produce a valid class for this row
