from enum import Enum
from typing import Any

from attrs import define, field
from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TimeElapsedColumn,
)
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from app.core.domain import ETLProtocol, ExtractMetadata

from .console import CONSOLE


class ProtocolRunStatus(Enum):
    RUNNING = (
        0,
        "bright_yellow",
        Spinner(name="dots", style="bright_yellow"),
    )
    COMPLETED = (
        1,
        "green",
        Text.from_markup("[green]:white_heavy_check_mark:"),
    )
    ERROR = 2, "bright_red", Text.from_markup("[bright_red]:warning:")

    @property
    def color(self) -> str:
        return self.value[1]

    @property
    def renderable(self) -> RenderableType:
        return self.value[2]


@define
class ETLProtocolUI:
    _etl_protocol: ETLProtocol[Any, Any, Any, Any, Any, Any] = field()
    _console: Console = field(default=CONSOLE)
    _status: ProtocolRunStatus = field(default=ProtocolRunStatus.RUNNING)
    _ui: RenderableType = field(init=False)
    _workflows_progress: Progress = field(init=False)
    _workflows_tasks: dict[str, TaskID] = field(factory=dict, init=False)

    def __attrs_post_init__(self) -> None:
        self._workflows_progress = Progress(
            "{task.description}",
            SpinnerColumn(),
            BarColumn(),
            TimeElapsedColumn(),
            console=self._console,
        )
        self._ui = self._build_ui()

    def __rich__(self) -> RenderableType:
        return self._ui

    def complete(self) -> None:
        self._status = ProtocolRunStatus.COMPLETED
        self.rebuild_ui()

    def error_out(self) -> None:
        self._status = ProtocolRunStatus.ERROR
        self.rebuild_ui()

    def rebuild_ui(self) -> None:
        self._ui = self._build_ui()

    def start_workflow(self, extract_meta: ExtractMetadata) -> None:
        task_id: TaskID = self._workflows_progress.add_task(
            description=f"[bright_yellow]{extract_meta.name}",
            total=None,
        )
        self._workflows_tasks[extract_meta.id] = task_id

    def stop_workflow(self, extract_meta: ExtractMetadata) -> None:
        task_id: TaskID = self._workflows_tasks[extract_meta.id]
        self._workflows_progress.update(
            task_id,
            completed=100,
            description=f"[green]{extract_meta.name}",
            total=100,
        )

    def _build_header(self) -> RenderableType:
        header: Table = Table.grid(padding=(0, 1))
        header.add_column(style=f"bold {self._status.color}", justify="right")
        header.add_column()
        header.add_row("Protocol ID:", self._etl_protocol.id)
        header.add_row("Description:", self._etl_protocol.description)
        header.add_row("Status: ", self._status.renderable)
        return header

    def _build_workflows_panel(self) -> RenderableType:
        return Panel(
            self._workflows_progress,
            border_style="bold cyan",
            title=f"[{self._status.color}]ETL Workflows",
        )

    def _build_ui(self) -> RenderableType:
        layout: Table = Table.grid(padding=(1, 0), expand=True)
        layout.add_row(self._build_header())
        layout.add_row(self._build_workflows_panel())
        return Panel(
            layout,
            border_style="bold cyan",
            title=f"[{self._status.color}]{self._etl_protocol.name}",
        )
