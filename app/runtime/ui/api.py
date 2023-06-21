from abc import ABCMeta, abstractmethod


class UI(metaclass=ABCMeta):
    """User interface provider."""

    @abstractmethod
    def start(self) -> None:
        """Start the UI.

        .. note::

            - Only called once.
            - Should not block the caller. Specifically, should not block the
              calling thread.

        :return: None.
        """
        ...
