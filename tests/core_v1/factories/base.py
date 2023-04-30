import uuid

import factory


class DomainObjectFactory(factory.Factory):
    """Base factory for most :class:`DomainObject` implementations."""

    class Meta:
        abstract = True


class IdentifiableDomainObjectFactory(DomainObjectFactory):
    """
    Base factory for most :class:`IdentifiableDomainObject` implementations.
    """

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))  # noqa: A003

    class Meta:
        abstract = True


class NamedDomainObjectFactory(DomainObjectFactory):
    """Base factory for most :class:`NamedDomainObject` implementations."""

    description = factory.Faker("sentence")

    class Meta:
        abstract = True
