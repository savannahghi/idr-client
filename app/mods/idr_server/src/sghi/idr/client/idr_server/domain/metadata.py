from attrs import define, field
from sghi.idr.client.core.domain import BaseDrainMetadata


@define(slots=True)
class IDRServerV1APIDrainMetadata(BaseDrainMetadata):
    _chunks: int = field()
    _org_unit_code: str = field()
    _org_unit_name: str = field()

    @property
    def chunks(self) -> int:
        return self._chunks

    @property
    def org_unit_code(self) -> str:
        return self._org_unit_code

    @property
    def org_unit_name(self) -> str:
        return self._org_unit_name
