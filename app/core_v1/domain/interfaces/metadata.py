from abc import ABCMeta, abstractmethod
from collections.abc import Mapping

from .base import DomainObject, IdentifiableDomainObject, NamedDomainObject

# =============================================================================
# METADATA INTERFACES
# =============================================================================


class MetadataObject(DomainObject, metaclass=ABCMeta):
    """Marker interface that identifies metadata containers.

    Define a :class:`DomainObject` that contains metadata. Metadata in this
    context refers to data that describes:

    * An operation to be performed by the client.
    * The resources needed as part of an operation to be performed.
    * Details of an operation that was performed by the client.
    * The data resulting from an operation performed by the client.
    """
    ...


class IdentifiableMetadataObject(
    MetadataObject, IdentifiableDomainObject, metaclass=ABCMeta,
):
    """A uniquely identifiable :class:`MetadataObject`."""
    ...


class DataSourceMetadata(
    NamedDomainObject, IdentifiableDomainObject, metaclass=ABCMeta,
):
    """:class:`Metadata <MetadataObject>` describing a :class:`DataSource`.

    This describes information used by the client to identify and/or initialize
    a `DataSource` to work with. It defines a writable property,
    :attr:`extract_metadata` that holds a Mapping of :class:`ExtractMetadata`
    instances associated with the aforementioned `DataSource`.
    """

    @property
    @abstractmethod
    def extract_metadata(self) -> Mapping[str, "ExtractMetadata"]:
        """Return a read only `Mapping` of :class:`ExtractMetadata` instances.

        Specifically, return a read only `Mapping` of the known
        `ExtractMetadata` instances that should be run against the
        :class:`DataSource` described by this instance.

        :return: A read only `Mapping` of the known `ExtractMetadata` instances
            that should be run against the `DataSource` described by this
            instance.
        """
        ...

    @extract_metadata.setter
    @abstractmethod
    def extract_metadata(
        self, extract_metas: Mapping[str, "ExtractMetadata"],
    ) -> None:
        """Define a `Mapping` containing :class:`ExtractMetadata` instances.

        Specifically, set this property with a read only `Mapping` of the known
        `ExtractMetadata` instances that should be run against the
        :class:`DataSource` described by this instance.

        :param extract_metas: A read only mapping containing the known
            `ExtraMetadata` instances that should be run against the
            `DataSource` described by this instance.

        :return: None
        """
        ...


class ExtractMetadata(
    NamedDomainObject, IdentifiableDomainObject, metaclass=ABCMeta,
):
    """:class:`Metadata<MetadataObject>` describing what to extract.

    This interface defines metadata describing data to be extracted from a
    :class:`DataSource`. A single `DataSourceMetadata` can have multiple
    `ExtractMetadata` instances associated with it.

    A read-only property, :attr:`data_source_metadata` is
    provided to allow access to the `DataSourceMetadata` instance describing
    the `DataSource` that the extract should be run against.
    """

    @property
    @abstractmethod
    def data_source_metadata(self) -> DataSourceMetadata:
        """Return a reference to the owning :class:`DataSourceMetadata`.

        Return a reference to the `DataSourceMetadata` that describes
        the :class:`DataSource` that this extract should be run against.

        :return: A reference to the owning `DataSourceMetadata` of this
            instance.
        """
        ...


class UploadContentMetadata(IdentifiableMetadataObject, metaclass=ABCMeta):
    """:class:`Metadata <MetadataObject>` describing an uploads content.

    This interface describes the details of the contents of an upload
    operation. That is, the details of a
    :class:`drainage operation<DataSinkStream>` to a :class:`DataSink`. A
    single upload, described by an :class:`UploadMetadata` instance, can have
    multiple `UploadContentMetadata` instances associated with it. This
    interface exist to allow :class:`data<CleanedData>` to be drained/uploaded
    to a `DataSink` in smaller sizes which is especially useful when working
    with :class:`data sources<DataSource>` that produce large amounts of data.

    A read-only property, :attr:`upload_metadata` is provided to allow access
    to the `UploadMetadata` instance that the `UploadContentMetadata` is part
    of.
    """

    @property
    @abstractmethod
    def upload_metadata(self) -> "UploadMetadata":
        """Return a reference to the owning :class:`UploadMetadata` instance.

        Return a reference to the `UploadMetadata` instance that this content
        metadata is part of.

        :return: A reference to the upload metadata instance that this content
            metadata instance is part of.
        """
        ...


class UploadMetadata(IdentifiableMetadataObject, metaclass=ABCMeta):
    """:class:`Metadata <MetadataObject>` describing an upload operation.

    This interface describes the details of an upload operation. That is,
    overall information about the details of a drainage operation to a
    :class:`DataSink` such as the content type of the data and the
    :class:`ExtractMetadata` instance that resulted in this
    :class:`data<CleanedData>`. The details of the actual data to be
    drained/uploaded is not described within this class's instances but rather
    it is described by the :class:`UploadContentMetadata` instance(s) attached
    to instances of this class.

    The `ExtractMetadata` instance that resulted in the data being
    drained/uploaded can be accessed using the read-only property,
    :attr:`extract_metadata`. The content type of the data can be accessed
    using the read-only property, :attr:`content_type`.
    """

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Return a brief identifier of the kind of data being operated on.

        Return a brief identifier of the kind of :class:`data<CleanedData>`
        being drained to a :class:`DataSink`.

        :return: A brief identifier of the kind of data being operated on.
        """
        ...

    @property
    @abstractmethod
    def extract_metadata(self) -> ExtractMetadata:
        """Return the uploads data, source :class:`ExtractMetadata` instance.

        Return the `ExtractMetadata` instance that resulted to this upload.

        :return: The extract metadata instance that resulted to this upload.
        """
        ...
