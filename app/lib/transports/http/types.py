from typing import (
    Any,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    Union,
)

_FileSpec = Tuple[
    str, bytes, str  # File name  # File content  # File content type
]


_Files = Union[Mapping[str, _FileSpec], Iterable[Tuple[str, _FileSpec]]]


class _OptionalAdapterRequestParams(TypedDict, total=False):
    data: Optional[Union[bytes, str, Mapping[str, Any]]]
    files: Optional[_Files]
    headers: Optional[Mapping[str, Optional[str]]]
    params: Optional[Mapping[str, Union[str, Sequence[str]]]]


class HTTPRequestParams(_OptionalAdapterRequestParams):
    expected_http_status_code: int
    method: str
    url: str
