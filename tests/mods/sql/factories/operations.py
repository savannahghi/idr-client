from typing import Any, Protocol

import factory
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.mods.sql.domain import (
    SimpleSQLDatabase,
    simple_data_source_stream_factory,
)
from tests.core.factories import DataSourceFactory

# =============================================================================
# TYPES
# =============================================================================


class _SampleDataGenerator(Protocol):
    def __call__(
        self,
        engine: Engine,
        size: int,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        ...


# =============================================================================
# HELPERS
# =============================================================================


def create_and_populate_sample_table(
    engine: Engine,
    size: int,
    **kwargs,
) -> None:
    """Given a database `Engine`, create and populate a table with sample data.

    .. note::
        This expects an `Engine` connected to an SQLite database.

    :param engine: An `Engine` connected to the database to populate with
        sample data. This function expects that the `Engine` is backed by an
        SQLite database.
    :param size: The sample size, i.e. The number of rows of the sample data
        to create.

    Supported keyword parameters include:

    * echo: Enable logging on the `Engine`. When set to `True`, will set
         the echo `Engine` attribute to `True`.

    :return: None.
    """
    engine.echo = kwargs.get("echo", False)
    with engine.connect().execution_options(
        logging_token="prelude",  # noqa: S106
    ) as connection:
        connection.execute(
            text("CREATE TABLE some_table (x int, y int, z int)"),
        )
        connection.execute(
            text("INSERT INTO some_table (x, y, z) VALUES (:x, :y, :z)"),
            [{"x": x, "y": x * 2, "z": x * 3} for x in range(size)],
        )
        connection.get_isolation_level()
        connection.commit()


# =============================================================================
# FACTORIES
# =============================================================================


class SimpleSQLDatabaseFactory(DataSourceFactory):
    """Factory for :class:`SimpleSQLDatabase`."""

    name = factory.Sequence(lambda _n: f"Test Database {_n}")
    description = "An SQL Lite in memory database for testing."
    data_source_stream_factory = simple_data_source_stream_factory
    engine = factory.LazyAttribute(lambda _o: create_engine(_o.database_url))

    # noinspection PyMethodParameters
    @factory.post_generation
    def add_sample_data(
        obj: SimpleSQLDatabase,  # type: ignore  # noqa: N805
        create: bool,
        extracted: bool | None,
        populate_func: _SampleDataGenerator = create_and_populate_sample_table,
        size: int = 5000,  # The size of the sample table to create
        **kwargs: Any,  # noqa: ANN401
    ) -> bool:
        """Populate the database with sample data for testing.

        :param create: This is always ignored regardless of its value.
        :param extracted: A flag indicating whether to populate the given
            database with sample data. The default behaviour is to not populate
            the database with sample data unless this parameter is explicitly
            set to ``True``.
        :param populate_func: A callable that does the actual population of the
            database with sample data. The callable should take a database
            `Engine` and a sample size as its first parameters. To override the
            default value, pass a custom value to the
            `add_sample_data__populate_func` parameter when calling this
            factory. See factory boy `docs <fboy_param_extraction_docs_>`_ for
            more details.
        :param size: The size of the sample data to create. This value
            typically refers to the number of rows of the sample data to create
            but the function defined by the `populate_func` may choose to
            ignore this value. To override the default value(5000), pass a
            custom value to the `add_sample_data__size` parameter when calling
            this factory. See factory boy `docs <fboy_param_extraction_docs_>`_
            for more details.
        :param kwargs: Extra arguments to pass to the `populate_func`.

        :return: None.

        .. _fboy_param_extraction_docs: https://factoryboy.readthedocs.io/en/stable/reference.html#extracting-parameters
        """
        if extracted is True:
            populate_func(obj.engine, size, **kwargs)
        return bool(extracted)

    class Meta:  # pyright: ignore
        model = SimpleSQLDatabase

    class Params:
        database_url = "sqlite+pysqlite:///:memory:"
        # There appears to be an issue with factory_boy. Enabling a Trait does
        # not trigger post-generation hooks.
        with_sample_data = factory.Trait(
            add_sample_data=True,
            engine=create_engine("sqlite+pysqlite:///:memory:"),
        )
