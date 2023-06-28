import io
import logging
from logging import Logger

from attrs import define, field
from sghi.idr.client.core.domain import BaseData, CleanedData, ExtractProcessor
from sghi.idr.client.sql.domain import PDDataFrame, SimpleSQLQuery


@define(slots=True)
class ParquetData(BaseData[io.BytesIO], CleanedData[io.BytesIO]):
    """Clean data packaged using the
    `Apache Parquet <https://parquet.apache.org/>`_ format.
    """

    @property
    def content_type(self) -> str:
        return "application/vnd.apache-parquet"


@define(slots=True, order=False)
class IDRServerExtractProcessor(
    ExtractProcessor[SimpleSQLQuery, PDDataFrame, ParquetData],
):
    _is_disposed: bool = field(default=False, init=False)
    _parquet_bytes: io.BytesIO = field(factory=io.BytesIO, init=False)

    def __attrs_post_init__(self) -> None:
        self._logger: Logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__qualname__}",
        )

    def process(
        self,
        raw_data: PDDataFrame,
        extract_metadata: SimpleSQLQuery,
    ) -> ParquetData:
        self._logger.info(
            'Process raw data with index %d, for extract metadata "%s".',
            raw_data.index,
            extract_metadata.name,
        )
        raw_data.content.to_parquet(
            path=self._parquet_bytes,
            engine="pyarrow",
            compression="brotli",
        )
        self._parquet_bytes.flush()

        # noinspection PyArgumentList
        return ParquetData(self._parquet_bytes, raw_data.index)

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    def dispose(self) -> None:
        self._is_disposed = True
        self._parquet_bytes.close()
        self._logger.debug("Disposal complete.")
