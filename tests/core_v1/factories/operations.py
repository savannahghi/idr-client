import factory

from .base import NamedDomainObjectFactory


class DataSinkFactory(NamedDomainObjectFactory):
    """Base factory for most :class:`DataSink` implementations."""

    name = factory.Sequence(lambda _n: f"Data Sink {_n}")
    description = factory.Sequence(lambda _n: f"Test Data Sink {_n}")

    class Meta:
        abstract = True


class DataSourceFactory(NamedDomainObjectFactory):
    """Base factory for most :class:`DataSource` implementations."""

    name = factory.Sequence(lambda _n: f"Data Source {_n}")
    description = factory.Sequence(lambda _n: f"Test Data Source {_n}")

    class Meta:
        abstract = True
