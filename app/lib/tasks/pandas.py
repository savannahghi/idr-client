from collections.abc import Sequence

import pandas as pd

from app.core.task import Task


class ChunkDataFrame(Task[pd.DataFrame, Sequence[pd.DataFrame]]):
    def execute(self, an_input: pd.DataFrame) -> Sequence[pd.DataFrame]:
        return (an_input,)
