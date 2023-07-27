from typing import Self

from attrs import field, frozen
from sghi.idr.client.core.domain import DrainMetadata, DrawMetadata


@frozen
class SimpleDrainMetadata(DrainMetadata):
    """A simple :class:`DrawMetadata` implementation."""

    _id: str = field()
    _draw_metadata: DrawMetadata = field()

    @property
    def id(self) -> str:  # noqa: A003
        return self._id

    @property
    def draw_metadata(self) -> DrawMetadata:
        return self._draw_metadata

    @classmethod
    def of(cls, id: str, draw_metadata: DrawMetadata) -> Self:  # noqa: A002
        """Factory method that create a new :class:`SimpleDrainMetadata`
        instance with the given properties.

        :param id: The id to assign to the created `SimpleDrainMetadata`
            instance.
        :param draw_metadata: The source `DrawMetadata` from which the created
            `SimpleDrainMetadata` should be derived from.

        :return: A `SimpleDrainMetadata` instance with the given properties.
        """
        return cls(
            id=id,  # pyright: ignore
            draw_metadata=draw_metadata,  # pyright: ignore
        )

    @classmethod
    def of_draw_metadata(cls, draw_metadata: DrawMetadata) -> Self:
        """Factory method that creates a new :class:`SimpleDrainMetadata` from
        the given :class:`DrawMetadata` instance. The :attr:`id` property of
        the returned `DrainMetadata` instance is equal to that of the given
        `DrawMetadata` instance.

        :param draw_metadata: A source `DrawMetadata` from which to derive a
            new `SimpleDrainMetadata` instance.

        :return: A `SimpleDrainMetadata` instance derived from the given
            `DrawMetadata` instance.
        """
        return cls.of(id=draw_metadata.id, draw_metadata=draw_metadata)
