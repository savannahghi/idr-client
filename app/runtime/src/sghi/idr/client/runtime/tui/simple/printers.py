import sys
import traceback

import click
import sghi.idr.client.core as app
from sghi.idr.client.runtime.constants import APP_VERBOSITY_REG_KEY


def print_debug(message: str, nl: bool = True) -> None:
    click.echo(click.style(message, fg="blue"), nl=nl)


def print_info(message: str) -> None:
    click.echo(click.style(message, fg="bright_blue"))


def print_error(error_message: str, exception: BaseException | None) -> None:
    verbosity: int = app.registry.get(APP_VERBOSITY_REG_KEY, 0)
    click.echo(click.style(error_message, fg="red"), file=sys.stderr)
    match verbosity:
        case 1 if exception is not None:
            click.secho(
                "".join(traceback.format_exception(exception, chain=False)),
                fg="magenta",
                file=sys.stderr,
            )
        case _ if verbosity > 1 and exception is not None:
            click.secho(
                "".join(traceback.format_exception(exception, chain=True)),
                fg="magenta",
                file=sys.stderr,
            )


def print_success(message: str) -> None:
    click.echo(click.style(message, fg="green"))
