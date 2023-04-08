from collections.abc import Iterable, Mapping, Sequence
from typing import Any, TypedDict, Union

_FileSpec = tuple[
    str, bytes, str  # File name  # File content  # File content type
]


_Files = Union[Mapping[str, _FileSpec], Iterable[tuple[str, _FileSpec]]]


class _OptionalAdapterRequestParams(TypedDict, total=False):
    data: bytes | str | Mapping[str, Any] | None
    files: _Files | None
    headers: Mapping[str, str | None] | None
    params: Mapping[str, str | Sequence[str]] | None


class HTTPRequestParams(_OptionalAdapterRequestParams):
    expected_http_status_code: int
    method: str
    url: str
