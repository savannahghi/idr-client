from argparse import ArgumentParser

from idr_client.lib import Pipeline
from idr_client.use_cases.main_pipeline import (
    CheckChangesFromETL,
    FetchMetadataFromServer,
    RunExtraction,
    RunTransformation,
    TransmitData,
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
        )
    )

    return parser


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    """
    The main entry point for this tool.

    :return: None.
    """

    parser = argparse_factory()
    parser.parse_args()

    etl_host_url: str = "http://127.0.0.1:8000"

    main_pipeline: Pipeline[str, object] = Pipeline(
        CheckChangesFromETL(),
        FetchMetadataFromServer(),
        RunExtraction(),
        RunTransformation(),
        TransmitData()
    )
    main_pipeline.execute(etl_host_url)


if __name__ == "__main__":
    main()
