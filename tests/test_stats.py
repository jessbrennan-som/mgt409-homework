import math

import pandas as pd
import pytest

from mgt409 import describe, moving_average, summary_table


def test_describe_basic():
    result = describe([2, 4, 4, 4, 5, 5, 7, 9])
    assert result["count"] == 8
    assert result["mean"] == pytest.approx(5.0)
    assert result["std"] == pytest.approx(2.138, abs=1e-3)
    assert result["min"] == 2
    assert result["median"] == pytest.approx(4.5)
    assert result["max"] == 9


def test_describe_single_value():
    result = describe([42])
    assert result["mean"] == 42
    assert result["std"] == 0.0


def test_describe_empty_raises():
    with pytest.raises(ValueError):
        describe([])


def test_moving_average():
    assert moving_average([1, 2, 3, 4, 5], 2) == pytest.approx([1.5, 2.5, 3.5, 4.5])
    assert moving_average([1, 2, 3, 4, 5], 5) == pytest.approx([3.0])


def test_moving_average_invalid_window():
    with pytest.raises(ValueError):
        moving_average([1, 2, 3], 0)
    with pytest.raises(ValueError):
        moving_average([1, 2, 3], 4)


def test_summary_table():
    frame = pd.DataFrame({"a": [1, 2, 3], "b": [10, 20, 30], "label": ["x", "y", "z"]})
    table = summary_table(frame)
    assert list(table.index) == ["a", "b"]
    assert table.loc["a", "mean"] == pytest.approx(2.0)
    assert table.loc["b", "max"] == 30
    assert math.isclose(table.loc["a", "std"], 1.0)
