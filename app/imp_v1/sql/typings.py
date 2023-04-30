from typing import Literal

ReadIsolationLevels = Literal[
    "READ COMMITTED",
    "READ UNCOMMITTED",
    "REPEATABLE READ",
]
