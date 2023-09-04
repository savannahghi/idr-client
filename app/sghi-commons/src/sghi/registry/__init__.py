"""
``Registry`` interface definition, implementing classes and helpers.
"""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from sghi.dispatch import Dispatcher, Signal
from sghi.exceptions import SGHIError
from sghi.utils import ensure_not_none

# =============================================================================
# EXCEPTIONS
# =============================================================================


class NoSuchRegistryItemError(SGHIError, LookupError):
    """Non-existent :class:`Registry` item access error.

    This is raised when trying to access or delete an item that does not exist
    in a ``Registry``.
    """

    def __init__(self, item_key: str, message: str | None = None) -> None:
        """Initialize a ``NoSuchRegistryItemError`` with the given properties.

        :param item_key: The key of the missing item.
        :param message: An optional message for the resulting exception.
            If none is provided, then a generic one is automatically generated.
        """
        self._item_key: str = ensure_not_none(
            item_key, "'item_key' MUST not be None.",
        )
        super().__init__(
            message=message or (
                "Item with key '%s' does not exist in the registry." %
                self._item_key
            ),
        )

    @property
    def item_key(self) -> str:
        """Return the missing item's key whose attempted access resulted in
        this exception being raised.

        :return: The missing item's key.
        """
        return self._item_key


# =============================================================================
# SIGNALS
# =============================================================================


@dataclass(frozen=True, slots=True)
class SetRegistryItemSignal(Signal):
    """Signal indicating the setting of an item in the :class:`Registry`.

    This signal is emitted when a new item is added or updated to the
    ``Registry``.
    """
    item_key: str = field()
    item_value: Any = field(repr=False)


@dataclass(frozen=True, slots=True)
class RemoveRegistryItemSignal(Signal):
    """Signal indicating the removal of an item from the :class:`Registry`.

    This signal is emitted when an item is removed from the ``Registry``.
    """
    item_key: str = field()


# =============================================================================
# REGISTRY INTERFACE
# =============================================================================


class Registry(metaclass=ABCMeta):
    """An interface representing a registry for storing key-value pairs.

    A ``Registry`` allows for storage and retrieval of values using unique
    keys. It supports basic dictionary-like operations and provides an
    interface for interacting with registered items.

    A ``Registry`` also comes bundled with a :class:`~sghi.dispatch.Dispatcher`
    whose responsibility is to emit :class:`signals<Signal>` whenever changes
    to the registry are made. It allows other components to subscribe to these
    signals and react accordingly.

    For a list of supported signals, see the :attr:`dispatcher` property.

    .. tip::

        Unless otherwise indicated, at runtime, there should be an instance of
        this class at :attr:`sghi.app.registry` ment to hold the main
        ``Registry`` for the executing application/tool.
    """

    __slots__ = ()

    @abstractmethod
    def __contains__(self, key: str) -> bool:
        """Check if the registry contains an item with the specified key.

        :param key: The key to check for.

        :return: ``True`` if the key exists in the registry, ``False``
            otherwise.
        """
        ...

    @abstractmethod
    def __delitem__(self, key: str) -> None:
        """Remove an item from the registry using the specified key.

        If successful, this will result in a :class:`RemoveRegistryItemSignal`
        being emitted.

        :param key: The key of the item to remove.

        :return: None.

        :raises NoSuchRegistryItemError: If the key does not exist in the
            registry.
        """
        ...

    @abstractmethod
    def __getitem__(self, key: str) -> Any:  # noqa: ANN401
        """
        Retrieve the value associated with the specified key from the registry.

        :param key: The key of the item to retrieve.

        :return: The value associated with the key.

        :raises NoSuchRegistryItemError: If the key does not exist in the
            registry.
        """
        ...

    @abstractmethod
    def __setitem__(self, key: str, value: Any) -> None:  # noqa: ANN401
        """Set the value associated with the specified key in the registry.

        If successful, this will result in a :class:`SetRegistryItemSignal`
        being emitted.

        :param key: The key of the item to set.
        :param value: The value to associate with the key.

        :return: None.
        """
        ...

    @property
    @abstractmethod
    def dispatcher(self) -> Dispatcher:
        """Get the :class:`Dispatcher` associated with the ``Registry``.

        The dispatcher is responsible for emitting signals when items are added
        or removed from the registry. It allows other components to subscribe
        to these signals and react accordingly.

        ----

        **Supported Signals**

        Each ``Registry`` implementation should at the very least support the
        following signals:

        - :class:`SetRegistryItemSignal` -> This signal is emitted when either
          a new item is added to the ``Registry``, or an existing item updated.
          It includes information about the item's key and value.
        - :class:`RemoveRegistryItemSignal` -> This signal is emitted when an
          item is removed from the registry. It includes information about the
          item's key.

        These signals provide a way for other parts of the application to react
        to changes in the registry, making the system more dynamic and
        responsive.


        :return: The dispatcher instance associated with the registry.
        """
        ...

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:  # noqa: ANN401
        """
        Retrieve the value associated with the specified key from the
        ``Registry``, with an optional default value if the key does not exist.

        :param key: The key of the item to retrieve.

        :param default: The default value to return if the key does not exist.
            Defaults to ``None`` when not specified.

        :return: The value associated with the key, or the default value.
        """
        ...

    @abstractmethod
    def pop(self, key: str, default: Any = None) -> Any:  # noqa: ANN401
        """
        Remove and return the value associated with the specified key from the
        ``Registry``, or the specified default if the key does not exist.

        .. note::

            A :class:`RemoveRegistryItemSignal` will only be emitted
            `if and only if` an item with the specified key existed in the
            ``Registry`` and was thus removed.

        :param key: The key of the item to remove.
        :param default: The default value to return if the key does not exist.
            Defaults to ``None`` when not specified.

        :return: The value associated with the key, or the default value.
        """
        ...

    @abstractmethod
    def setdefault(self, key: str, value: Any) -> Any:  # noqa: ANN401
        """
        Retrieve the value associated with the specified key from the
        ``Registry``, or set it if the key does not exist.

        .. note::

            A :class:`SetRegistryItemSignal` will only be emitted
            `if and only if` an item with the specified key does not exist in
            the ``Registry`` and thus the new default value was set.

        :param key: The key of the item to retrieve or set.
        :param value: The value to associate with the key if it does not exist.

        :return: The value associated with the key, or the newly set value.
        """
        ...

    @staticmethod
    def of(dispatcher: Dispatcher | None = None) -> Registry:
        """Factory method to create ``Registry`` instances.

        :param dispatcher: An optional ``Dispatcher`` instance to associate
            with the registry. A new ``Dispatcher`` instance will be created if
            not specified.

        :return: A ``Registry`` instance.
        """
        return _RegistryImp(dispatcher=dispatcher or Dispatcher.of())


# =============================================================================
# REGISTRY IMPLEMENTATIONS
# =============================================================================


class _RegistryImp(Registry):
    """An implementation of the Registry interface."""

    __slots__ = ("_dispatcher", "_items")

    def __init__(self, dispatcher: Dispatcher) -> None:
        super().__init__()
        self._dispatcher: Dispatcher = ensure_not_none(
            dispatcher, "'dispatcher' MUST not be None.",
        )
        self._items: dict[str, Any] = {}

    def __contains__(self, key: str) -> bool:
        return key in self._items

    def __delitem__(self, key: str) -> None:
        ensure_not_none(key, "'key' MUST not be None.")
        try:
            del self._items[key]
            self.dispatcher.send(RemoveRegistryItemSignal(item_key=key))
        except KeyError:
            raise NoSuchRegistryItemError(item_key=key) from None

    def __getitem__(self, key: str) -> Any:  # noqa: ANN401
        ensure_not_none(key, "'key' MUST not be None.")
        try:
            return self._items[key]
        except KeyError:
            raise NoSuchRegistryItemError(item_key=key) from None

    def __setitem__(self, key: str, value: Any) -> None:  # noqa: ANN401
        ensure_not_none(key, "'key' MUST not be None.")
        self._items[key] = value
        self.dispatcher.send(
            SetRegistryItemSignal(item_key=key, item_value=value),
        )

    @property
    def dispatcher(self) -> Dispatcher:
        return self._dispatcher

    def get(self, key: str, default: Any = None) -> Any:  # noqa: ANN401
        ensure_not_none(key, "'key' MUST not be None.")
        return self._items.get(key, default)

    def pop(self, key: str, default: Any = None) -> Any:  # noqa: ANN401
        ensure_not_none(key, "'key' MUST not be None.")
        try:
            value = self._items.pop(key)
            self._dispatcher.send(RemoveRegistryItemSignal(item_key=key))
            return value
        except KeyError:
            return default

    def setdefault(self, key: str, value: Any) -> Any:  # noqa: ANN401
        ensure_not_none(key, "'key' MUST not be None.")
        try:
            return self[key]
        except LookupError:
            self[key] = value
            return value


# =============================================================================
# MODULE EXPORTS
# =============================================================================


__all__ = (
    "NoSuchRegistryItemError",
    "Registry",
    "RemoveRegistryItemSignal",
    "SetRegistryItemSignal",
)
