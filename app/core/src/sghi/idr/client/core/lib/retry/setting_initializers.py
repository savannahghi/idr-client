from typing import Any

from ..config import ImproperlyConfiguredError, SettingInitializer
from .constants import DEFAULT_RETRY_CONFIG, RETRY_CONFIG_KEY
from .types import RetryConfig


class RetryInitializer(SettingInitializer):
    """
    A :class:`SettingInitializer` that initializes and validates the global
    retry configuration. If no retry configuration is provided, this
    initializer also sets a default one.
    """

    @property
    def setting(self) -> str:
        return RETRY_CONFIG_KEY

    def execute(self, an_input: RetryConfig | None) -> RetryConfig:
        if an_input is None:
            return DEFAULT_RETRY_CONFIG
        self._sanitize_and_load_config(an_input)
        return an_input

    def _sanitize_and_load_config(self, config: RetryConfig) -> None:
        if not isinstance(config, dict):
            err_msg: str = f'The setting "{self.setting}" is invalid.'
            raise ImproperlyConfiguredError(message=err_msg)
        if "default_deadline" in config and config["default_deadline"]:
            self._ensure_value_is_float_and_greater_than_zero(
                config=config,
                setting="default_deadline",
            )
        if "default_initial_delay" in config:
            self._ensure_value_is_float_and_greater_than_zero(
                config=config,
                setting="default_initial_delay",
            )
        if "default_maximum_delay" in config:
            self._ensure_value_is_float_and_greater_than_zero(
                config=config,
                setting="default_maximum_delay",
            )
        if "default_multiplicative_factor" in config:
            self._ensure_value_is_float_and_greater_than_zero(
                config=config,
                setting="default_multiplicative_factor",
            )
        enable_retries = config.get("enable_retries", True)
        config["enable_retries"] = bool(
            enable_retries is True or enable_retries == "true",
        )

    def _ensure_value_is_float_and_greater_than_zero(
        self,
        config: RetryConfig,
        setting: str,
    ) -> None:
        value = config[setting]
        if not (self._is_float(value) and float(value) > 0.0):
            err_msg: str = (
                'The setting "{}" must be a subtype of float and greater than '
                "zero".format(setting)
            )
            raise ImproperlyConfiguredError(message=err_msg)
        config[setting] = float(value)

    @staticmethod
    def _is_float(value: Any) -> bool:  # noqa: ANN401
        try:
            float(value)
            return True
        except ValueError:
            return False
