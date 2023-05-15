import pyarrow as pa
from attrs import define, field

from app.core_v1.domain import BaseData, CleanedData, ExtractProcessor
from app.imp_v1.sql.domain import PDDataFrame, SimpleSQLQuery


@define(slots=True)
class ParquetData(BaseData, CleanedData[pa.BufferReader]):
    """Clean data packaged using the
    `Apache Parquet <https://parquet.apache.org/>`_ format.
    """

    ...


@define(slots=True, order=False)
class IDRServerExtractProcessor(
    ExtractProcessor[SimpleSQLQuery, PDDataFrame, ParquetData],
):
    _is_disposed: bool = field(default=False, init=False)

    def __attrs_post_init__(self) -> None:
        # noinspection PyArgumentList
        self._writer: pa.BufferedOutputStream = pa.BufferedOutputStream()
        self._reader: pa.BufferReader = pa.BufferReader(self._writer)

    def process(
        self,
        raw_data: PDDataFrame,
        extract_metadata: SimpleSQLQuery,
    ) -> ParquetData:
        raw_data.content.to_parquet(
            path=self._writer,
            engine="pyarrow",
            compression="brotli",
        )
        # noinspection PyArgumentList
        return ParquetData(self._reader)

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    def dispose(self) -> None:
        self._is_disposed = True
        self._reader.close()
        self._writer.close()
