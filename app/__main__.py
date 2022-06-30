from argparse import ArgumentParser
from typing import Any

import app
from app.core import Transport
from app.lib import HTTPTransport, Pipeline
from app.use_cases.main_pipeline import (
    FetchMetadata,
    ProcessExtracts,
    RunExtraction,
    UploadExtracts,
)

# =============================================================================
# HELPERS
# =============================================================================


def argparse_factory(prog_name: str = "idr_client") -> ArgumentParser:
    """Returns a new ArgumentParser instance configured for use with this tool.

    :param prog_name: An optional name to be used as the program name.
    :return: An ArgumentParser instance for use with this program.
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
        default="config.yaml",
        help=(
            "The location of the application config file. Only yaml files are "
            "supported currently (default: %(default)s)."
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
        "--version", action="version", version="%(prog)s 1.0.0"
    )

    return parser


def main_pipeline_factory() -> Pipeline[None, Any]:
    transport: Transport = HTTPTransport()
    return Pipeline(
        FetchMetadata(transport=transport),
        RunExtraction(),
        ProcessExtracts(),
        UploadExtracts(transport=transport),
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
    parser.parse_args()

    app.setup()
    main_pipeline: Pipeline[None, Any] = main_pipeline_factory()
    main_pipeline.execute(None)
    print("Done ...")


if __name__ == "__main__":  # pragma: no cover
    main()
