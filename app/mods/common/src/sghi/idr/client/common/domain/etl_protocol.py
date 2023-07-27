import uuid
from collections.abc import Callable, Iterable
from typing import Any, Generic, Self, TypeVar, assert_never

from attrs import define, field
from sghi.idr.client.core.domain import (
    BaseIdentifiableDomainObject,
    BaseNamedDomainObject,
    CleanedData,
    DataProcessor,
    DataSink,
    DataSinkMetadata,
    DataSinkSelector,
    DataSource,
    DataSourceMetadata,
    DrainMetadata,
    DrainMetadataFactory,
    DrawMetadata,
    ETLProtocol,
    ETLProtocolSupplier,
    MetadataConsumer,
    MetadataSupplier,
    RawData,
)
from sghi.idr.client.core.lib import ImproperlyConfiguredError, type_fqn

from ..lib import (
    ETL_PROTOCOL_DEFINITIONS_CONFIG_KEY,
    ETL_PROTOCOL_FACTORIES_CONFIG_KEY,
    ETLProtocolFactory,
    ProtocolDefinition,
)
from .operations import NoOpDataProcessor, NullDataSink
from .terminals import (
    NullMetadataConsumer,
    SelectAllDataSinkSelector,
    SimpleDrainMetadataFactory,
)

# =============================================================================
# TYPES
# =============================================================================

_CD = TypeVar("_CD", bound=CleanedData)
_DM = TypeVar("_DM", bound=DataSourceMetadata)
_DS = TypeVar("_DS", bound=DataSinkMetadata)
_EM = TypeVar("_EM", bound=DrawMetadata)
_RD = TypeVar("_RD", bound=RawData)
_UM = TypeVar("_UM", bound=DrainMetadata)

_EP = ETLProtocol[Any, Any, Any, Any, Any, Any]


# =============================================================================
# HELPERS
# =============================================================================

# =============================================================================
# CONCRETE ETL PROTOCOL DEFINITIONS
# =============================================================================


@define(slots=True, order=False)
class SimpleETLProtocol(
    BaseIdentifiableDomainObject,
    BaseNamedDomainObject,
    ETLProtocol[_DM, _EM, _RD, _CD, _UM, _DS],
    Generic[_DM, _EM, _RD, _CD, _UM, _DS],
):
    """A simple implementation of an :class:`ETLProtocol`."""

    _data_sink_factory: Callable[[_DS], DataSink[_DS, _UM, _CD]] = field()
    _data_source_factory: Callable[[_DM], DataSource[_DM, _EM, _RD]] = field()
    _data_processor_factory: Callable[
        [],
        DataProcessor[_EM, _RD, _CD],
    ] = field()
    _drain_metadata_factory: DrainMetadataFactory[_UM, _EM] = field()
    _metadata_consumer: MetadataConsumer[_UM] = field()
    _metadata_supplier: MetadataSupplier[_DS, _DM, _EM] = field()
    _data_sink_selector: DataSinkSelector[_DS, _DM, _CD, _UM] = field(
        factory=SelectAllDataSinkSelector, kw_only=True,
    )

    @property
    def data_sink_factory(self) -> Callable[[_DS], DataSink[_DS, _UM, _CD]]:
        return self._data_sink_factory

    @property
    def data_sink_selector(self) -> DataSinkSelector[_DS, _DM, _CD, _UM]:
        return self._data_sink_selector

    @property
    def data_source_factory(
        self,
    ) -> Callable[[_DM], DataSource[_DM, _EM, _RD]]:
        return self._data_source_factory

    @property
    def data_processor_factory(
        self,
    ) -> Callable[[], DataProcessor[_EM, _RD, _CD]]:
        return self._data_processor_factory

    @property
    def metadata_consumer(self) -> MetadataConsumer[_UM]:
        return self._metadata_consumer

    @property
    def metadata_supplier(self) -> MetadataSupplier[_DS, _DM, _EM]:
        return self._metadata_supplier

    @property
    def drain_metadata_factory(self) -> DrainMetadataFactory[_UM, _EM]:
        return self._drain_metadata_factory

    @classmethod
    def of(
        cls,
        id: str,  # noqa: A002
        name: str,
        data_source_factory: Callable[[_DM], DataSource[_DM, _EM, _RD]],
        metadata_supplier: MetadataSupplier[_DS, _DM, _EM],
        description: str | None = None,
        data_sink_factory: Callable[
            [_DS], DataSink[_DS, _UM, _CD],
        ] | None = None,
        data_processor_factory: Callable[
            [], DataProcessor[_EM, _RD, _CD],
        ] | None = None,
        drain_metadata_factory: DrainMetadataFactory[_UM, _EM] | None = None,
        metadata_consumer: MetadataConsumer[_UM] | None = None,
        data_sink_selector: DataSinkSelector[_DS, _DM, _CD, _UM] | None = None,
    ) -> Self:
        """Construct a new :class:`ETLProtocol` with the given properties."""
        return cls(
            id=id,  # pyright: ignore
            name=name,  # pyright: ignore
            description=description,  # pyright: ignore
            data_sink_factory=(  # pyright: ignore
                data_sink_factory or NullDataSink.of_data_sink_meta
            ),
            data_source_factory=data_source_factory,  # pyright: ignore
            data_processor_factory=(  # pyright: ignore
                data_processor_factory or NoOpDataProcessor
            ),
            drain_metadata_factory=(  # pyright: ignore
                drain_metadata_factory or SimpleDrainMetadataFactory()
            ),
            metadata_consumer=(  # pyright: ignore
                metadata_consumer or NullMetadataConsumer.of()
            ),
            metadata_supplier=metadata_supplier,  # pyright: ignore
            data_sink_selector=(  # pyright: ignore
                data_sink_selector or SelectAllDataSinkSelector()
            ),
        )

    @classmethod
    def of_minimal(
        cls,
        name: str,
        data_source_factory: Callable[[_DM], DataSource[_DM, _EM, _RD]],
        metadata_supplier: MetadataSupplier[_DS, _DM, _EM],
        id: str | None = None,  # noqa: A002
        description: str | None = None,
    ) -> Self:
        return cls.of(
            id=id or str(uuid.uuid4()),
            name=name,
            description=description,
            data_source_factory=data_source_factory,
            metadata_supplier=metadata_supplier,
        )


# =============================================================================
# ETL PROTOCOL SUPPLIERS
# =============================================================================


class FromDefinitionsETLProtocolSupplier(ETLProtocolSupplier):
    """
    Load :class:`ETLProtocol` instances from ETLProtocol definitions on the
    config.
    """

    def get_protocols(self) -> Iterable[_EP]:
        from sghi.idr.client.core import settings

        proto_definitions: Iterable[ProtocolDefinition]
        proto_definitions = settings.get(
            setting=ETL_PROTOCOL_DEFINITIONS_CONFIG_KEY,
            default=(),
        )
        return map(
            self._proto_definition_to_proto_instance,
            proto_definitions,
        )

    @classmethod
    def _proto_definition_to_proto_instance(
        cls,
        protocol_definition: ProtocolDefinition,
    ) -> _EP:
        dmf_def = protocol_definition["drain_metadata_factory"]
        dmf: DrainMetadataFactory = cls._get_data_meta_factory_instance(
            dmf_def,
        )
        return SimpleETLProtocol.of(
            id=protocol_definition["id"],
            name=protocol_definition["name"],
            description=protocol_definition.get("description"),
            data_sink_factory=protocol_definition["data_sink_factory"],
            data_source_factory=protocol_definition["data_source_factory"],
            data_processor_factory=protocol_definition[
                "data_processor_factory"
            ],
            metadata_consumer=protocol_definition[
                "metadata_consumer_factory"
            ](),
            metadata_supplier=protocol_definition[
                "metadata_supplier_factory"
            ](),
            drain_metadata_factory=dmf,
        )

    @staticmethod
    def _get_data_meta_factory_instance(
        dmf_def: DrainMetadataFactory | Callable[[], DrainMetadataFactory],
    ) -> DrainMetadataFactory:
        match dmf_def:
            case DrainMetadataFactory():
                return dmf_def
            case Callable():
                return dmf_def()
            case _:
                assert_never(dmf_def)  # pyright: ignore


class FromFactoriesETLProtocolSupplier(ETLProtocolSupplier):
    """
    Load :class:`ETLProtocol` instances from ETLProtocol factories on the
    config.
    """

    def get_protocols(self) -> Iterable[_EP]:
        from sghi.idr.client.core import settings

        proto_factories: Iterable[ETLProtocolFactory]
        proto_factories = settings.get(
            setting=ETL_PROTOCOL_FACTORIES_CONFIG_KEY,
            default=(),
        )

        return map(self._proto_factory_to_instance, proto_factories)

    @staticmethod
    def _proto_factory_to_instance(proto_factory: ETLProtocolFactory) -> _EP:
        try:
            _etl_proto_instance: _EP = proto_factory()
        except Exception as exp:  # noqa: BLE001
            _err_msg: str = (
                "Unable to create an ETLProtocol instance from factory. The "
                "cause was: '{}'".format(str(exp))
            )
            raise RuntimeError(_err_msg) from exp

        if not isinstance(_etl_proto_instance, ETLProtocol):
            _err_msg: str = (
                "Invalid ETLProtocol, the factory '{}' returned an instance "
                "that is not a subclass of "
                "'sghi.idr.client.core.domain.ETLProtocol'.".format(
                    type_fqn(proto_factory),
                )
            )
            raise ImproperlyConfiguredError(message=_err_msg)

        return _etl_proto_instance
