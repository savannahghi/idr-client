"""
Multiple-producer-multiple-accept signal-dispatching *heavily* inspired by
`PyDispatcher <https://grass.osgeo.org/grass83/manuals/libpython/pydispatch.html>`_
and :doc:`Django dispatch<django:topics/signals>`
"""
from __future__ import annotations

import logging
import weakref
from abc import ABCMeta, abstractmethod
from logging import Logger
from threading import RLock
from typing import (
    TYPE_CHECKING,
    Generic,
    Protocol,
    TypeGuard,
    TypeVar,
    runtime_checkable,
)

from ..utils import ensure_not_none, type_fqn

if TYPE_CHECKING:
    from collections.abc import Iterable


# =============================================================================
# TYPES
# =============================================================================

_ST_contra = TypeVar("_ST_contra", bound="Signal", contravariant=True)


@runtime_checkable
class Receiver(Protocol[_ST_contra]):
    """A callable object that receives and processes :class:`signals<Signal>`.

    A ``Receiver`` should accept o ``Signal`` as its sole argument and return
    ``None``.
    """

    def __call__(self, signal: _ST_contra) -> None:
        """Receive and process a :class:`Signal`.

        :param signal: The signal being received and processed.

        :return: None.
        """
        ...


# =============================================================================
# INTERFACES
# =============================================================================


class Signal(metaclass=ABCMeta):
    """An occurrence of interest.

    This class serves as a base for defining custom ``Signal`` classes that
    represent specific occurrences or events in an application.
    """

    __slots__ = ()


class Dispatcher(metaclass=ABCMeta):
    """
    An abstract class defining the interface for a :class:`Signal` dispatcher.

    ``Signal`` dispatchers are responsible for connecting and disconnecting
    :class:`receivers<Receiver>` to be notified when a signal is triggered, as
    well as sending signals to the registered receivers.
    """

    __slots__ = ()

    @abstractmethod
    def connect(
        self,
        signal_type: type[_ST_contra],
        receiver: Receiver[_ST_contra],
        weak: bool = True,
    ) -> None:
        """
        Register a :class:`receiver<Receiver>` to be notified of occurrences of
        the specific :class:`signal type<Signal>`.

        :param signal_type: The type of ``Signal`` to connect the receiver to.
        :param receiver: The ``Receiver`` function to connect.
        :param weak: Whether to use weak references for the connection.

        :return: None,
        """
        ...

    @abstractmethod
    def disconnect(
        self,
        signal_type: type[_ST_contra],
        receiver: Receiver[_ST_contra],
    ) -> None:
        """
        Detach a :class:`Receiver` function from a specific :class:`Signal`
        type.

        .. admonition:: **To Implementors**
            :class: note

            The disconnect should detach the ``Receiver`` from this
            ``Dispatcher`` regardless of whether the ``Receiver`` was connected
            using weak references.

        :param signal_type: The type of ``Signal`` to disconnect the receiver
            from.
        :param receiver: The ``Receiver`` function to disconnect.

        :return: None.
        """
        ...

    @abstractmethod
    def send(self, signal: Signal, robust: bool = True) -> None:
        """
        Send a :class:`Signal` to all connected :class:`receivers<Receiver>`.

        If robust is set to ``False`` and a ``Receiver`` raises an error, the
        error propagates back through send, terminating the dispatch loop. So
        it's possible that all receivers won't be called if an error is raised.

        :param signal: The ``Signal`` to send.
        :param robust: Whether to handle errors robustly.

        :return: None.
        """
        ...

    @staticmethod
    def of() -> Dispatcher:
        """Create and return a new :class:`Dispatcher` instance.

        .. admonition:: Info

            The returned ``Dispatcher`` is threadsafe.

        :return: A ``Dispatcher`` instance.
        """
        return _DispatcherImp()


# =============================================================================
# DECORATORS
# =============================================================================

class connect(Generic[_ST_contra]):  # noqa :N801
    """
    A decorator for registering :class:`receivers<Receiver>` to be notified
    when :class:`signals<Signal>` occur.

    This decorator simplifies the process of connecting a receiver function to
    a specific signal type in a :class:`dispatcher<Dispatcher>`. It is used to
    mark a function as a receiver and specify the associated signal type and
    dispatcher.
    """

    __slots__ = ("_signal_type", "_dispatcher", "_weak")

    def __init__(
        self,
        signal_type: type[_ST_contra],
        /,
        dispatcher: Dispatcher | None = None,
        weak: bool = True,
    ) -> None:
        """Initialize a new instance of ``connect`` decorator.

        :param signal_type: The type of ``Signal`` to connect the receiver to.
        :param dispatcher: The ``Dispatcher`` instance to connect the receiver
            in. If not provided, will default to the value of
            :attr:`sghi.app.dispatcher`.
        :param weak: Whether to use weak references for the connection.
        """
        super().__init__()
        from sghi.app import dispatcher as app_dispatcher

        self._signal_type: type[_ST_contra] = ensure_not_none(
            signal_type, "'signal_type' MUST not be None.",
        )
        self._dispatcher: Dispatcher = dispatcher or app_dispatcher
        self._weak: bool = weak

    def __call__(self, f: Receiver[_ST_contra]) -> Receiver[_ST_contra]:
        """
        Attach a :class:`receiver<Receiver>` function to a :class:`Dispatcher`.

        :param f: The function to be attached to a ``Dispatcher``.

        :return: The decorated function.
        """
        ensure_not_none(f, "'f' MUST not be None.")

        self._dispatcher.connect(self._signal_type, f, weak=self._weak)

        return f


# =============================================================================
# DISPATCH IMPLEMENTATIONS
# =============================================================================

class _DispatcherImp(Dispatcher):
    """The default implementation of the :class:`Dispatcher` interface."""

    __slots__ = ("_receivers", "_lock", "_logger", "_has_dead_receivers")

    def __init__(self) -> None:
        super().__init__()
        self._receivers: dict[
            type[Signal], set[Receiver | weakref.ReferenceType[Receiver]],
        ] = {}
        self._lock: RLock = RLock()
        self._logger: Logger = logging.getLogger(type_fqn(self.__class__))
        self._has_dead_receivers: bool = False

    def connect(
        self,
        signal_type: type[_ST_contra],
        receiver: Receiver[_ST_contra],
        weak: bool = True,
    ) -> None:
        self._logger.debug("Connect receiver, '%s'.", type_fqn(receiver))
        _receiver: Receiver[_ST_contra] | weakref.ReferenceType[Receiver[_ST_contra]]  # noqa: E501
        _receiver = receiver
        if weak:
            ref = weakref.ref
            receiver_object = receiver
            # Check for bound methods
            if hasattr(receiver, "__self__") and hasattr(receiver, "__func__"):
                ref = weakref.WeakMethod
                receiver_object = receiver.__self__  # type: ignore
            _receiver = ref(receiver)
            weakref.finalize(receiver_object, self._mark_dead_receiver_present)
        with self._lock:
            self._clear_dead_receivers()
            self._receivers.setdefault(signal_type, set()).add(_receiver)

    def disconnect(
        self,
        signal_type: type[_ST_contra],
        receiver: Receiver[_ST_contra],
    ) -> None:
        self._logger.debug("Disconnect receiver, '%s'.", type_fqn(receiver))
        with self._lock:
            self._clear_dead_receivers()
            self._receivers.get(signal_type, set()).discard(receiver)

    def send(self, signal: Signal, robust: bool = True) -> None:
        for receiver in self._live_receivers(type(signal)):
            try:
                receiver(signal)
            except Exception:
                if not robust:
                    raise
                self._logger.exception(
                    "Error executing receiver '%s'.", type_fqn(receiver),
                )

    def _clear_dead_receivers(self) -> None:
        with self._lock:
            if not self._has_dead_receivers:
                return
            for _signal_type, _receivers in self._receivers.items():
                self._receivers[_signal_type] = set(
                    filter(self._is_life_receiver, _receivers),
                )
            self._has_dead_receivers = False

    def _live_receivers(
        self,
        signal_type: type[_ST_contra],
    ) -> Iterable[Receiver[_ST_contra]]:
        with self._lock:
            self._clear_dead_receivers()
            receivers: set[Receiver[_ST_contra] | weakref.ReferenceType[Receiver[_ST_contra]]]  # noqa: E501
            receivers = self._receivers.get(signal_type, set())
            return filter(
                self._is_live, map(self._dereference_as_necessary, receivers),
            )

    def _mark_dead_receiver_present(self) -> None:
        with self._lock:
            self._has_dead_receivers = True

    @staticmethod
    def _dereference_as_necessary(
        receiver: Receiver[_ST_contra] | weakref.ReferenceType[Receiver[_ST_contra]],  # noqa: E501
    ) -> Receiver[_ST_contra] | None:
        # Dereference, if weak reference
        return (
            receiver()
            if isinstance(receiver, weakref.ReferenceType)
            else receiver
        )

    @staticmethod
    def _is_live(
        receiver: Receiver[_ST_contra] | None,
    ) -> TypeGuard[Receiver[_ST_contra]]:
        return receiver is not None

    @staticmethod
    def _is_life_receiver(receiver: Receiver | weakref.ReferenceType) -> bool:
        return not (
            isinstance(receiver, weakref.ReferenceType) and receiver() is None,
        )

# =============================================================================
# MODULE EXPORTS
# =============================================================================


__all__ = [
    "Dispatcher",
    "Receiver",
    "Signal",
    "connect",
]
