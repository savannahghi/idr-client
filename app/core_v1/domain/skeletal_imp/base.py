from abc import ABCMeta

from attrs import define, field

from ..interfaces import (
    DomainObject,
    IdentifiableDomainObject,
    NamedDomainObject,
)


@define(slots=False)
class BaseDomainObject(DomainObject, metaclass=ABCMeta):
    """Base skeletal implementation for most :class:`DomainObject` s."""
    ...


@define(slots=False)
class BaseIdentifiableDomainObject(
    BaseDomainObject, IdentifiableDomainObject, metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`IdentifiableDomainObject` s.
    """

    _id: str = field()

    @property
    def id(self) -> str:  # noqa: A003
        return self._id


@define(slots=False)
class BaseNamedDomainObject(
    BaseDomainObject, NamedDomainObject, metaclass=ABCMeta,
):
    """Base skeletal implementation for most :class:`NamedDomainObject` s."""

    _name: str = field()
    _description: str | None = field(default=None, kw_only=True)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str | None:
        return self._description
