from typing import Callable, Optional, TypedDict

Predicate = Callable[[BaseException], bool]


class RetryConfig(TypedDict, total=False):
    """Structure of the Retry configuration mappings."""

    default_deadline: Optional[float]
    default_initial_delay: float
    default_maximum_delay: float
    default_multiplicative_factor: float
    enable_retries: bool
