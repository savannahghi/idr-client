from collections.abc import Callable, Iterable, Sequence
from functools import cache
from typing import Any, Final, TypedDict

from sghi.idr.client.core.domain import (
    DataProcessor,
    DataSink,
    DataSinkMetadata,
    DataSource,
    DataSourceMetadata,
    DrainMetadataFactory,
    ETLProtocol,
    MetadataConsumer,
    MetadataSupplier,
)
from sghi.idr.client.core.lib import (
    ImproperlyConfiguredError,
    SettingInitializer,
    import_string,
)
from typing_inspect import typed_dict_keys

# =============================================================================
# TYPES
# =============================================================================


ETLProtocolFactory = Callable[[], ETLProtocol]


class _ProtocolDefinitionOptional(TypedDict, total=False):
    description: str | None


class _RawProtocolDefinition(_ProtocolDefinitionOptional, total=True):
    id: str  # noqa: A003
    name: str
    data_sink_factory: str  # Callable[[DataSinkMetadata], DataSink]
    data_source_factory: str  # Callable[[DataSourceMetadata], DataSource]
    data_processor_factory: str  # Callable[[], DataProcessor]
    drain_metadata_factory: str  # DrainMetadataFactory
    metadata_consumer_factory: str  # Callable[[], MetadataConsumer]
    metadata_supplier_factory: str  # Callable[[], MetadataSupplier]


class ProtocolDefinition(_ProtocolDefinitionOptional, total=True):
    id: str  # noqa: A003
    name: str
    data_sink_factory: Callable[[DataSinkMetadata], DataSink]
    data_source_factory: Callable[[DataSourceMetadata], DataSource]
    data_processor_factory: Callable[[], DataProcessor]
    drain_metadata_factory: DrainMetadataFactory | Callable[
        [],
        DrainMetadataFactory,
    ]
    metadata_consumer_factory: Callable[[], MetadataConsumer]
    metadata_supplier_factory: Callable[[], MetadataSupplier]


# =============================================================================
# CONSTANTS
# =============================================================================

_UNKNOWN_STR: Final[str] = "UNKNOWN"

ETL_PROTOCOL_DEFINITIONS_CONFIG_KEY: Final[str] = "ETL_PROTOCOL_DEFINITIONS"

ETL_PROTOCOL_FACTORIES_CONFIG_KEY: Final[str] = "ETL_PROTOCOL_FACTORIES"


# =============================================================================
# HELPERS
# =============================================================================


@cache
def _get_required_proto_definition_fields() -> set[str]:
    all_fields: set[str] = set(
        typed_dict_keys(_RawProtocolDefinition).keys(),
    )
    optional_fields: set[str] = set(
        typed_dict_keys(_ProtocolDefinitionOptional).keys(),
    )
    return all_fields.difference(optional_fields)


# =============================================================================
# SETTINGS INITIALIZERS
# =============================================================================


class ETLProtocolDefinitionsInitializer(SettingInitializer):
    """
    :class:`SettingInitializer` that loads :class:`ETLProtocol` definitions for
    later instantiation.
    """

    @property
    def has_secrets(self) -> bool:
        return False

    @property
    def setting(self) -> str:
        return ETL_PROTOCOL_DEFINITIONS_CONFIG_KEY

    def execute(
        self,
        an_input: Iterable[_RawProtocolDefinition] | None,
    ) -> Iterable[ProtocolDefinition]:
        return tuple(map(self._mapping_to_definition, an_input or ()))

    def _mapping_to_definition(
        self,
        raw_protocol_definition: _RawProtocolDefinition,
    ) -> ProtocolDefinition:
        self._check_raw_definition(raw_protocol_definition)
        return {
            "id": raw_protocol_definition["id"],
            "name": raw_protocol_definition["name"],
            "description": raw_protocol_definition.get("description"),
            "data_sink_factory": self._load_entry_point(
                raw_protocol_definition["data_sink_factory"],
                item_name="data_sink_factory",
            ),
            "data_source_factory": self._load_entry_point(
                raw_protocol_definition["data_source_factory"],
                item_name="data_source_factory",
            ),
            "data_processor_factory": self._load_entry_point(
                raw_protocol_definition["data_processor_factory"],
                item_name="data_processor_factory",
            ),
            "drain_metadata_factory": self._load_entry_point(
                raw_protocol_definition["drain_metadata_factory"],
                item_name="drain_metadata_factory",
            ),
            "metadata_consumer_factory": self._load_entry_point(
                raw_protocol_definition["metadata_consumer_factory"],
                item_name="metadata_consumer_factory",
            ),
            "metadata_supplier_factory": self._load_entry_point(
                raw_protocol_definition["metadata_supplier_factory"],
                item_name="metadata_supplier_factory",
            ),
        }

    @staticmethod
    def _check_raw_definition(
        raw_protocol_definition: _RawProtocolDefinition,
    ) -> None:
        required_fields: set[str] = _get_required_proto_definition_fields()
        missing_fields: set[str] = required_fields.difference(
            set(raw_protocol_definition.keys()),
        )
        if len(missing_fields) > 0:
            _err_msg: str = (
                "The following missing fields must be provided for each "
                "protocol definition: '{}'.".format(",".join(missing_fields))
            )
            raise ImproperlyConfiguredError(message=_err_msg)

    @staticmethod
    def _load_entry_point(
        item_dotted_path: str,
        item_name: str,
    ) -> Any:  # noqa: ANN401
        try:
            return import_string(dotted_path=item_dotted_path)
        except ImportError as exp:
            _err_msg: str = (
                "Invalid {} given. '{}' does not seem to be a valid path."
                .format(item_name, item_dotted_path)
            )
            raise ImproperlyConfiguredError(message=_err_msg) from exp


class ETLProtocolFactoriesInitializer(SettingInitializer):
    """
    :class:`SettingInitializer` that loads :class:`ETLProtocol` factories for
    later instantiation.
    """

    @property
    def has_secrets(self) -> bool:
        return False

    @property
    def setting(self) -> str:
        return ETL_PROTOCOL_FACTORIES_CONFIG_KEY

    def execute(
        self,
        an_input: Sequence[str] | None,
    ) -> Sequence[ETLProtocolFactory]:
        protocol_factories: Sequence[ETLProtocolFactory] = list(
            map(self._dotted_path_to_factory, an_input or ()),
        )
        return protocol_factories

    @staticmethod
    def _dotted_path_to_factory(
        protocol_dotted_path: str,
    ) -> ETLProtocolFactory:
        try:
            etl_protocol_factory: ETLProtocolFactory
            etl_protocol_factory = import_string(protocol_dotted_path)
            return etl_protocol_factory
        except ImportError as exp:
            _err_msg: str = '"{}" does not seem to be a valid path.'.format(
                protocol_dotted_path,
            )
            raise ImproperlyConfiguredError(message=_err_msg) from exp
