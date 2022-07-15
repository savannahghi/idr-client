from argparse import ArgumentParser
from typing import Any, Optional, Sequence

import app
from app.core import DataSourceType, Transport
from app.lib import Pipeline
from app.use_cases.main_pipeline import (
    FetchMetadata,
    RunExtraction,
    UploadExtracts,
)

from .__version__ import __title__, __version__

# =============================================================================
# HELPERS
# =============================================================================


def argparse_factory(prog_name: str = __title__) -> ArgumentParser:
    """Returns a new ArgumentParser instance configured for use with this app.

    :param prog_name: An optional name to be used as the program name.
    :return: An ArgumentParser instance for use with this app.
    """

    parser = ArgumentParser(
        prog=prog_name,
        description=(
            "A tool used to extract data from a source(most likely a database)"
            ", transform it and transmit it to a central server for analysis "
            "and/or storage."
        ),
    )
    parser.add_argument(
        "-c",
        "--config",
        help=(
            "The location of the application config file. Only yaml files are "
            "supported currently."
        ),
        type=str,
    )
    parser.add_argument(
        "-o",
        "--out_dir",
        default="out",
        help=(
            "The output directory where generated xls-forms are persisted "
            "(default: %(default)s)."
        ),
        type=str,
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Disable printers from producing any output on std out.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=(
            "The level of output that printers should produce "
            "(default: %(default)d)."
        ),
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )

    return parser


def main_pipeline_factory(
    transport: Optional[Transport] = None,
) -> Pipeline[Sequence[DataSourceType], Any]:
    """A factory for the main application pipeline.

    Returns a fully initialized pipeline ready for use. An optional
    :class:`transport <Transport>` instance can be given for use by the
    pipeline tasks. If one, isn't provided, then one will be retrieved from
    the app registry or an error raised if none is set.

    :param transport: An optional transport for use by the pipeline tasks.

    :return: A fully initialized main pipeline instance ready for use.

    :raise ImproperlyConfiguredError: If no transport was provided and the
        app default transport hasn't been set.
    """
    _transport: Transport
    _transport = (
        transport
        or app.registry.get_default_transport_factory_or_raise(  # noqa
            error_message="The default transport factory is required by the "
            "main application pipeline."
        )()
    )
    return Pipeline(
        FetchMetadata(transport=_transport),
        RunExtraction(),
        UploadExtracts(transport=_transport),
    )


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:  # pragma: no cover
    """
    The main entry point for this tool.

    :return: None.
    """

    parser = argparse_factory()
    args = parser.parse_args()

    app.setup(config_file_path=args.config)
    transport_factory = app.registry.get_default_transport_factory_or_raise()
    with transport_factory() as transport:
        main_pipeline: Pipeline[
            Sequence[DataSourceType], Any
        ] = main_pipeline_factory(transport=transport)
        main_pipeline.execute(tuple(app.registry.data_source_types.values()))
    print("Done ...")


if __name__ == "__main__":  # pragma: no cover
    main()
