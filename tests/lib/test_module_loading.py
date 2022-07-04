import pytest

from app.lib import Config, import_string


def test_correct_return_value_on_valid_dotted_path() -> None:
    """
    Assert that when given a valid dotted path as input, ``import_string``
    returns the correct class or attribute.
    """
    assert import_string("app.lib.Config") is Config
    assert (
        import_string("app.lib.module_loading.import_string") is import_string
    )  # noqa


def test_correct_expected_behavior_on_invalid_dotted_path() -> None:
    """
    Assert that an ``ImportError`` is raised when an invalid dotted path is
    given as input to ``import_string``.
    """
    with pytest.raises(ImportError):
        import_string("aninvalidpath")
    with pytest.raises(ImportError):
        import_string("app.no_such")
