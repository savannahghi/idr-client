import io

from attrs import define, field

from app.core_v1.domain import BaseData, CleanedData, ExtractProcessor
from app.imp_v1.sql.domain import PDDataFrame, SimpleSQLQuery


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

    def process(
        self,
        raw_data: PDDataFrame,
        extract_metadata: SimpleSQLQuery,
    ) -> ParquetData:
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
