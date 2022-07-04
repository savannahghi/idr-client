from typing import Sequence

import pytest

from app.lib import ensure_not_none, ensure_not_none_nor_empty


def test_ensure_not_none_returns_input_value_if_valid() -> None:
    """
    Assert ``ensure_not_none`` returns the input value if the input is not
    ``None``.
    """
    value1: str = "A value"
    value2: Sequence[int] = [1, 2, 3, 4, 5]
    value3: int = 0
    value4: bool = False

    assert ensure_not_none(value1) == value1
    assert ensure_not_none(value2) == value2
    assert ensure_not_none(value3) == value3
    assert ensure_not_none(value4) == value4


def test_ensure_not_none_fails_on_invalid_input() -> None:
    """
    Assert that ``ensure_not_none`` raises ``ValueError`` when given a ``None``
    value as input.
    """
    with pytest.raises(ValueError) as exp_info1:
        ensure_not_none(None)
    with pytest.raises(ValueError) as exp_info2:
        ensure_not_none(None, message="Invalid.")

    assert exp_info1.value.args[0] == '"value" cannot be None.'
    assert exp_info2.value.args[0] == "Invalid."


def test_ensure_not_none_nor_empty_returns_input_value_if_valid() -> None:
    """
    Assert ``ensure_not_none_nor_empty`` returns the input value if the input
    is not ``None`` or empty.
    """
    value1: str = "A value"
    value2: Sequence[int] = [1, 2, 3, 4, 5]

    assert ensure_not_none_nor_empty(value1) == value1
    assert ensure_not_none_nor_empty(value2) == value2


def test_ensure_not_none_nor_empty_fails_on_invalid_input() -> None:
    """
    Assert that ``ensure_not_none_nor_empty`` raises ``ValueError`` when given
    a ``None`` or empty value as input.
    """
    with pytest.raises(ValueError) as exp_info1:
        ensure_not_none_nor_empty(None)  # type: ignore
    with pytest.raises(ValueError) as exp_info2:
        ensure_not_none_nor_empty(None, message="Invalid.")  # type: ignore
    with pytest.raises(ValueError) as exp_info3:
        ensure_not_none_nor_empty("")
    with pytest.raises(ValueError) as exp_info4:
        ensure_not_none_nor_empty([], message="Invalid.")

    assert exp_info1.value.args[0] == '"value" cannot be None or empty.'
    assert exp_info2.value.args[0] == "Invalid."
    assert exp_info3.value.args[0] == '"value" cannot be None or empty.'
    assert exp_info4.value.args[0] == "Invalid."
