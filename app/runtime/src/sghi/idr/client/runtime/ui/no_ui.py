from attrs import frozen

from .api import UI


@frozen
class NoUI(UI):
    """:class:`UI` implementation that has no UI."""

    def start(self) -> None:
        pass
