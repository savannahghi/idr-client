import pytest

from app.core import Task
from app.lib import Config, Consumer, import_string, import_string_as_klass


def test_correct_return_value_on_valid_dotted_path1() -> None:
    """
    Assert that when given a valid dotted path as input, ``import_string``
    returns the correct class or attribute.
    """
    assert import_string("app.lib.Config") is Config
    assert (
        import_string("app.lib.module_loading.import_string") is import_string
    )  # noqa


def test_correct_expected_behavior_on_invalid_dotted_path1() -> None:
    """
    Assert that an ``ImportError`` is raised when an invalid dotted path is
    given as input to ``import_string``.
    """
    with pytest.raises(ImportError):
        import_string("aninvalidpath")
    with pytest.raises(ImportError):
        import_string("app.no_such")


def test_correct_return_value_on_valid_dotted_path2() -> None:
    """
    Assert that when given a valid dotted path as input,
    ``import_string_import_string_as_klass`` returns the correct class.
    """
    assert import_string_as_klass("app.lib.Config", Config) is Config
    assert import_string_as_klass("app.lib.Consumer", Task) is Consumer


def test_correct_expected_behavior_on_invalid_dotted_path2() -> None:
    """
    Assert that an ``ImportError`` or ``TypeError`` is raised when an invalid
    dotted path is given as input to ``import_import_string_as_klass``.
    """
    with pytest.raises(ImportError):
        import_string_as_klass("aninvalidpath", Config)
    with pytest.raises(TypeError):
        import_string_as_klass(
            "app.lib.module_loading.import_string",
            import_string,  # type: ignore
        )
    with pytest.raises(TypeError):
        import_string_as_klass("app.lib.Config", Task)
