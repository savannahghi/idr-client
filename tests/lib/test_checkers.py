from typing import TYPE_CHECKING, SupportsFloat

import pytest

from app.lib import (
    ensure_greater_than,
    ensure_not_none,
    ensure_not_none_nor_empty,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


def test_ensure_greater_than_return_value_on_valid_input() -> None:
    """
    Assert ``ensure_greater_than`` returns the input value if the given
    ``value`` is greater than the given ``base_value``.
    """

    assert ensure_greater_than(1, 0) == 1
    assert ensure_greater_than(0, -1) == 0
    assert ensure_greater_than(-0.0, -1.0) == 0.0
    assert ensure_greater_than(0.999999, 0) == 0.999999
    assert ensure_greater_than(-19, -30) == -19


def test_ensure_fails_on_invalid_input() -> None:
    """
    Assert ``ensure_not_none`` raises ``ValueError`` when the given ``value``
    is not greater than the given ``base_value``.
    """

    inputs: Iterable[tuple[SupportsFloat, SupportsFloat]] = (
        (0, 1),
        (-1, 0),
        (-1.0, -0.0),
        (0, 0.999999),
        (-30, -19),
    )
    for value, base_value in inputs:
        message: str = "{} must be greater than {}".format(
            value,
            base_value,
        )
        with pytest.raises(ValueError, match="be greater than") as exp_info1:
            ensure_greater_than(value, base_value, message=message)

        assert exp_info1.value.args[0] == message.format(value, base_value)


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
    with pytest.raises(ValueError, match="cannot be None") as exp_info1:
        ensure_not_none(None)
    with pytest.raises(ValueError, match="Invalid") as exp_info2:
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
    with pytest.raises(ValueError, match="cannot be None or emp") as exp_info1:
        ensure_not_none_nor_empty(None)  # type: ignore
    with pytest.raises(ValueError, match="Invalid") as exp_info2:
        ensure_not_none_nor_empty(None, message="Invalid.")  # type: ignore
    with pytest.raises(ValueError, match="cannot be None or emp") as exp_info3:
        ensure_not_none_nor_empty("")
    with pytest.raises(ValueError, match="Invalid") as exp_info4:
        ensure_not_none_nor_empty([], message="Invalid.")

    assert exp_info1.value.args[0] == '"value" cannot be None or empty.'
    assert exp_info2.value.args[0] == "Invalid."
    assert exp_info3.value.args[0] == '"value" cannot be None or empty.'
    assert exp_info4.value.args[0] == "Invalid."
