from typing import Any, Mapping, Optional, Sequence, TypedDict, Union


class _OptionalAdapterRequestParams(TypedDict, total=False):
    data: Optional[Union[bytes, str, Mapping[str, Any]]]
    headers: Optional[Mapping[str, Optional[str]]]
    params: Optional[Mapping[str, Union[str, Sequence[str]]]]


class HTTPRequestParams(_OptionalAdapterRequestParams):
    expected_http_status_code: int
    method: str
    url: str
