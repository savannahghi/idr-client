from abc import ABCMeta, abstractmethod

# =============================================================================
# BASE INTERFACES
# =============================================================================


class DomainObject(metaclass=ABCMeta):  # noqa: B024
    """Marker interface that identifies a domain object.

    All domain objects should implement this interface.
    """

    ...


class IdentifiableDomainObject(DomainObject, metaclass=ABCMeta):
    """A uniquely identifiable :class:`DomainObject`.

    Define a domain object that can be uniquely identified using a key.
    Contains one read-only property :attr:`id` that should return a string
    that uniquely identifies this object among other objects of the same
    class/type.
    """

    @property
    @abstractmethod
    def id(self) -> str:  # noqa: A003
        """Return a key that uniquely identifies this domain object.

        :return: A key that uniquely identifies this domain object.
        """
        ...


class NamedDomainObject(DomainObject, metaclass=ABCMeta):
    """A :class:`DomainObject` that has a name and an optional description.

    Define a `DomainObject` that has a brief but descriptive name and an
    optional longer description. Contains two readonly properties, :attr:`name`
    and :attr:`description`.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return a brief descriptive name for this domain object.

        :return: A brief descriptive name for this domain object.
        """
        ...

    @property
    @abstractmethod
    def description(self) -> str | None:
        """Return an optional, longer description for this item.

        :return: An optional longer description for this item.
        """
        ...
