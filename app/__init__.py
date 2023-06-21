from collections.abc import Mapping, Sequence
from typing import Any, Final

from app.lib import AppRegistry, Config, SettingInitializer

registry: Final[AppRegistry] = AppRegistry()
"""
The application registry. Provides lookup for important resources and services
within the application.
"""

settings: Final[Config] = None  # type: ignore
"""
The application configurations. This value is only available after a
successful application set up. That is, after ``app.setup()`` completes
successfully.
"""


def setup(
    settings: Mapping[str, Any] | None = None,
    settings_initializers: Sequence[SettingInitializer] | None = None,
    **kwargs,
) -> None:
    """Prepare the runtime and ready the application for use.

    :param settings: An optional mapping of settings and their values. When not
        provided, the runtime defaults as well as defaults set by the given
        setting initializers will be used instead.
    :param settings_initializers: An optional sequence of setting initializers
        to execute during runtime setup. Default initializers(set by the
        runtime) are always executed unless the `disable_default_initializers`
        param is set to ``True``.
    :param kwargs: Additional keyword arguments to pass to the implementing
        function.

    :return: None.
    """
    err_message = (
        "'setup' is not implemented. Runtimes or implementing applications "
        "should override this function with a suitable implementation."
    )
    raise NotImplementedError(err_message)
