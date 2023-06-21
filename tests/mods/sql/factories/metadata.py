from collections.abc import Mapping
from typing import Any, cast

import factory
from toolz.curried import map, pipe

from app.mods.sql.domain import (
    SimpleSQLDatabaseDescriptor,
    SimpleSQLQuery,
    simple_data_source_stream_factory,
)
from tests.core_v1.factories import (
    DataSourceMetadataFactory,
    ExtractMetadataFactory,
)


class SimpleSQLDatabaseDescriptorFactory(DataSourceMetadataFactory):
    """Factory for :class:`SimpleSQLDatabaseDescriptor`."""

    name = factory.Sequence(lambda _n: f"Test Database {_n}")
    description = "An SQL Lite in memory database for testing."
    database_url = "sqlite+pysqlite:///:memory:"
    isolation_level = "REPEATABLE READ"
    logging_name = None
    data_source_stream_factory = simple_data_source_stream_factory

    class Meta:  # pyright: ignore
        model = SimpleSQLDatabaseDescriptor

    # noinspection PyMethodParameters
    @factory.post_generation
    def queries_count(
        obj: SimpleSQLDatabaseDescriptor,  # type: ignore  # noqa: N805
        create: bool,
        extracted: int | None,
        **kwargs: Any,  # noqa: ANN401
    ) -> Mapping[str, SimpleSQLQuery]:
        """Generate and attach dummy/test `SimpleSQLQuery` instances associated
        with the created `SimpleSQLDatabaseDescriptor` instance.

        if not specified, this hook defaults to creating 5 instances.

        :param create: This is always ignored regardless of its value.
        :param extracted: The number of `SimpleSQLQuery` instances to create.
        :param kwargs: Extra key word arguments to pass to the generated
            `SimpleSQLQuery` instances.

        :return: A mapping of the generated `SimpleSQLQuery` instances.
        """
        _sq: SimpleSQLQuery
        kwargs["data_source_metadata"] = obj
        kwargs["ensure_attached"] = False
        sql_queries: Mapping[str, SimpleSQLQuery] = pipe(  # type: ignore
            range(5 if extracted is None else extracted),
            map(lambda _: SimpleSQLQueryFactory(**kwargs)),
            map(lambda _sq: (_sq.id, _sq)),
            dict,
        )
        obj.extract_metadata = sql_queries
        return sql_queries


class SimpleSQLQueryFactory(ExtractMetadataFactory):
    """Factory for :class:`SimpleSQLQueryFactory`."""

    name = factory.Sequence(lambda _n: f"Test Query {_n}")
    description = "Test SQL Query."  # pyright: ignore
    data_source_metadata = factory.SubFactory(
        SimpleSQLDatabaseDescriptorFactory,
        queries_count=0,
    )
    raw_sql_query = "SELECT x, y FROM test"
    yield_per = None
    logging_token = None
    isolation_level = None

    @factory.lazy_attribute
    def description(self) -> str:
        dsm: SimpleSQLDatabaseDescriptor = cast(
            SimpleSQLDatabaseDescriptor,
            self.data_source_metadata,
        )
        return f"Retrieve data from the {dsm.name} database."

    # noinspection PyMethodParameters
    @factory.post_generation
    def ensure_attached(
        obj: SimpleSQLQuery,  # type: ignore  # noqa: N805
        create: bool,
        extracted: bool | None,
        **kwargs: Any,  # noqa: ANN401
    ) -> bool:
        """Ensure that the created `SimpleSQLQuery` instance is attached to the
        `SimpleSQLDatabaseDescriptor` instance that owns it.

        If the value is not set (i.e. is `False`), then no changes are made to
        the parent `SimpleSQLDatabaseDescriptor` instance, and it will be left
        as is. If not set, (i.e. is `True`) and the created `SimpleSQLQuery`
        instance is not in the parent `SimpleSQLDatabaseDescriptor` instance,
        then it will be added.

        :param create: This is always ignored regardless of its value.
        :param extracted: A flag indicating whether to attach the created
            instance to its parent.
        :param kwargs: This is always ignored.

        :return: The attachment status.
        """
        attach = True if extracted is None else extracted
        if attach and obj.id not in obj.data_source_metadata.extract_metadata:
            sql_queries = dict(obj.data_source_metadata.extract_metadata)
            sql_queries[obj.id] = obj
            obj.data_source_metadata.extract_metadata = sql_queries

        return attach

    class Meta:  # pyright: ignore
        model = SimpleSQLQuery
        strategy = factory.BUILD_STRATEGY

    class Params:
        from_xy_table = factory.Trait(
            name="Get all XYs",
            description='Retrieve all rows from the "xy" table',
            raw_sql_query="SELECT x, y FROM xy",
        )
