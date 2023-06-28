from typing import Final

from .types import RetryConfig

RETRY_CONFIG_KEY: Final[str] = "RETRY"

DEFAULT_DEADLINE: Final[float] = 60.0 * 5  # In seconds

DEFAULT_INITIAL_DELAY: Final[float] = 1.0  # In seconds

DEFAULT_MAXIMUM_DELAY: Final[float] = 60.0  # In seconds

DEFAULT_MULTIPLICATIVE_FACTOR: Final[float] = 2.0

DEFAULT_RETRY_CONFIG: Final[RetryConfig] = {
    "default_deadline": DEFAULT_DEADLINE,
    "default_initial_delay": DEFAULT_INITIAL_DELAY,
    "default_maximum_delay": DEFAULT_MAXIMUM_DELAY,
    "default_multiplicative_factor": DEFAULT_MULTIPLICATIVE_FACTOR,
    "enable_retries": True,
}
