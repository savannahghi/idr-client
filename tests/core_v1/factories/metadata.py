import factory

from .base import (
    DomainObjectFactory,
    IdentifiableDomainObjectFactory,
    NamedDomainObjectFactory,
)


class MetadataObjectFactory(DomainObjectFactory):
    """Base factory for most :class:`MetadataObject` implementations."""

    class Meta:
        abstract = True


class IdentifiableMetadataObjectFactory(
    MetadataObjectFactory,
    IdentifiableDomainObjectFactory,
):
    """
    Base factory for most :class:`IdentifiableMetadataObject` implementations.
    """

    class Meta:
        abstract = True


class DataSourceMetadataFactory(
    NamedDomainObjectFactory,
    IdentifiableMetadataObjectFactory,
):
    """Base factory for most :class:`DataSourceMetadata` implementations."""

    name = factory.Sequence(lambda _n: f"Data Source {_n}")
    description = factory.Sequence(lambda _n: f"Test Data Source {_n}.")

    class Meta:
        abstract = True


class ExtractMetadataFactory(
    NamedDomainObjectFactory,
    IdentifiableMetadataObjectFactory,
):
    """Base factory for most :class:`ExtractMetadata` implementations."""

    name = factory.Sequence(lambda _n: f"Extract Metadata {_n}")
    description = factory.Sequence(lambda _n: f"Test Extract Metadata {_n}.")

    class Meta:
        abstract = True


class UploadContentMetadataFactory(IdentifiableMetadataObjectFactory):
    """Base factory for most :class:`UploadContentMetadata` implementations."""

    class Meta:
        abstract = True


class UploadMetadataFactory(IdentifiableMetadataObjectFactory):
    """Base factory for most :class:`UploadMetadata` implementations."""

    class Meta:
        abstract = True
