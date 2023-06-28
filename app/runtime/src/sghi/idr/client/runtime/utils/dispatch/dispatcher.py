import logging
from abc import ABCMeta
from collections.abc import Callable, Mapping
from logging import Logger
from typing import Any, TypeVar

import wrapt
from attrs import define, field
from sghi.idr.client.core.lib import type_fqn

# =============================================================================
# TYPES
# =============================================================================

_S = TypeVar("_S", bound="Signal")

Receiver = Callable[[_S], None]


# =============================================================================
# DISPATCHER & SIGNAL IMPLEMENTATIONS
# =============================================================================


class Signal(metaclass=ABCMeta):  # noqa: B024
    ...


@define(eq=False, order=False)
class Dispatcher:
    _receivers: dict[type[_S], set[Receiver]] = field(  # type: ignore
        factory=dict,
        init=False,
    )
    _logger: Logger = field(init=False)

    def __attrs_post_init__(self) -> None:
        self._logger: Logger = logging.getLogger(type_fqn(self.__class__))

    @wrapt.decorator()
    def __call__(
        self,
        wrapped: type[_S],
        # Types and default values are included on the rest of the arguments to
        # quiet pyright.
        instance: Any = None,  # noqa: ANN401
        args: tuple[Receiver] = (),  # type: ignore
        kwargs: Mapping[str, Receiver] | None = None,
    ) -> None:
        self.connect(wrapped, args[0])

    def connect(self, signal_type: type[_S], receiver: Receiver[_S]) -> None:
        self._logger.info("Add receiver of type '%s'.", type_fqn(signal_type))
        self._receivers.setdefault(signal_type, set()).add(receiver)

    def disconnect(
        self,
        signal_type: type[_S],
        receiver: Receiver[_S],
    ) -> None:
        self._logger.info(
            "Remove receiver of type '%s'.",
            type_fqn(signal_type),
        )
        self._receivers.get(signal_type, set()).discard(receiver)

    def send(self, signal: Signal) -> None:
        for receiver in self._receivers.get(type(signal), set()):
            try:
                receiver(signal)
            except Exception:
                _err_msg: str = (
                    f"Error executing receiver '{type_fqn(receiver)}'."
                )
                self._logger.exception(_err_msg)
