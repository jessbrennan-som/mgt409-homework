"""Basic descriptive-statistics helpers used across homework assignments."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


def describe(values: Sequence[float]) -> dict[str, float]:
    """Return common summary statistics for a 1-D sequence of numbers.

    Uses the sample standard deviation (ddof=1) to match the convention used
    in most introductory statistics courses.
    """
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError("describe() requires at least one value")

    return {
        "count": float(arr.size),
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=1)) if arr.size > 1 else 0.0,
        "min": float(arr.min()),
        "median": float(np.median(arr)),
        "max": float(arr.max()),
    }


def moving_average(values: Sequence[float], window: int) -> list[float]:
    """Return the simple moving average of ``values`` over ``window`` periods."""
    if window < 1:
        raise ValueError("window must be a positive integer")
    arr = np.asarray(values, dtype=float)
    if arr.size < window:
        raise ValueError("window cannot be larger than the number of values")

    kernel = np.ones(window) / window
    return list(np.convolve(arr, kernel, mode="valid"))


def summary_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a tidy summary (mean/std/min/max) for each numeric column."""
    numeric = frame.select_dtypes(include="number")
    if numeric.empty:
        raise ValueError("summary_table() needs at least one numeric column")

    return pd.DataFrame(
        {
            "mean": numeric.mean(),
            "std": numeric.std(ddof=1),
            "min": numeric.min(),
            "max": numeric.max(),
        }
    )
