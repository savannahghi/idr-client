from unittest import TestCase as _TestCase
from unittest.mock import patch

from app.lib import AppRegistry, Config

from .factories import config_factory as _cf


class TestCase(_TestCase):
    """A project-specific ``TestCase``.

    Extend the default :class:`unittest.TestCase` to provide the following:

    * Configure the execution environment at the class level, once for the
      whole ``TestCase``. This is similar to calling :func:`app.setup`.
    * Add a class method, :meth:`config_factory` that returns a
      :class:`Config <app.lib.Config>` instance used to configure the
      execution environment of this ``TestCase`` instances.
    """

    @classmethod
    def config_factory(cls) -> Config:
        """Return a ``Config`` instance.

        Return a :class:`~app.lib.Config` instance used to configure the
        execution environment of this ``TestCase`` instances.

        :return: a Config instance.
        """
        return Config(settings=_cf())

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class fixture before running the tests in the class.

        Extend the default implementation by setting up a patch for the
        application settings and registry using the value returned by the
        :meth:`config_factory` class method. The patch is accessible through
        the class attribute :attr:`config_patcher` for interested subclasses.

        .. warning::
            It is highly encouraged that subclasses extending this method call
            ``super()`` to avoid weird, unpredictable behaviour during test
            runs caused by misconfigured execution environments.

        :return: None.
        """
        super().setUpClass()
        config_patcher = patch.multiple(
            "app",
            registry=AppRegistry(),
            settings=cls.config_factory(),
        )
        config_patcher.start()
        cls.config_patcher = config_patcher
        cls.addClassCleanup(config_patcher.stop)
