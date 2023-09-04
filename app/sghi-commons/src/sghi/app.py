"""
Global state definitions for SGHI applications/tools.

This module defines global properties important to an application. For all
intents and purposes, these properties should be treated and thought of as
constants. Any assignments to these properties should be done inside the
:func:`setup` function(see below).

This module also defines a single abstract method, :func:`setup` whose main
purpose is to initialize and set up the application/tool readying it for use.
It should be called first before proceeding with the normal usage of the
application/tool. The setup function defined here is abstract and thus not
useful. Applications/tools should provide a valid implementation and monkey
patch it before first use. Whether multiple calls to the `setup` should be
allowed is not defined and is left to the application/tool implementors to
decide.
"""
from collections.abc import Mapping, Sequence
from typing import Any, Final

from .config import Config, SettingInitializer
from .dispatch import Dispatcher
from .registry import Registry

# =============================================================================
# GLOBAL APPLICATION/TOOL CONSTANTS
# =============================================================================


dispatcher: Final[Dispatcher] = Dispatcher.of()
"""The main application :class:`dispatcher<sghi.dispatch.Dispatcher>`."""

registry: Final[Registry] = Registry.of()
"""The main application :class:`registry<sghi.registry.Registry>`."""

conf: Final[Config] = Config.of_awaiting_setup()
"""The application configurations.

.. important::

    A usable value is only available after a
    successful application set up. That is, after :func:`sghi.app.setup` or
    equivalent completes successfully.
"""


# =============================================================================
# SETUP FUNTION
# =============================================================================


def setup(
    settings: Mapping[str, Any] | None = None,
    settings_initializers: Sequence[SettingInitializer] | None = None,
    **kwargs,
) -> None:
    """Prepare the application/tool and ready it for use.

    After this function completes successfully, the application/tool should
    be considered set up and normal usage may proceed.

    .. important::

        This method is not implemented, and invocations will result in an
        exception being raised. Runtimes/implementing applications should
        monkey patch this method before first use with a valid implementation.

    :param settings: An optional mapping of settings and their values. When not
        provided, the runtime defaults as well as defaults set by the given
        setting initializers will be used instead.
    :param settings_initializers: An optional sequence of setting initializers
        to execute during runtime setup.
    :param kwargs: Additional keyword arguments to pass to the implementing
        function.

    :return: None.
    """
    err_message = (
        "'setup' is not implemented. Implementing applications or tools "
        "should override this function with a suitable implementation."
    )
    raise NotImplementedError(err_message)
