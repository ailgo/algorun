import logging

import click

from algorun.core import proc
from algorun.core.sandbox import ComposeSandbox

logger = logging.getLogger(__name__)


@click.command(
    "goal",
    short_help="Run the Algorand goal CLI against your mainnet node.",
    context_settings={
        "ignore_unknown_options": True,
    },
)
@click.option(
    "--console",
    is_flag=True,
    help="Open a Bash console so you can execute multiple goal commands and/or interact with a filesystem.",
    default=False,
)
@click.argument("goal_args", nargs=-1, type=click.UNPROCESSED)
def goal_command(*, console: bool, goal_args: list[str]) -> None:
    """
    Run the Algorand goal CLI against the mainnet node.

    Look at https://developer.algorand.org/docs/clis/goal/goal/ for more information.
    """
    try:
        proc.run(["docker", "version"], bad_return_code_error_message="Docker engine isn't running; please start it.")
    except OSError as ex:
        # an IOError (such as PermissionError or FileNotFoundError) will only occur if "docker"
        # isn't an executable in the user's path, which means docker isn't installed
        raise click.ClickException(
            "Docker not found; please install Docker and add to path.\n"
            "See https://docs.docker.com/get-docker/ for more information."
        ) from ex
    if console:
        if goal_args:
            logger.warning("--console opens an interactive shell, remaining arguments are being ignored")
        logger.info("Opening Bash console on the algod node; execute `exit` to return to original console")
        result = proc.run_interactive("docker exec -it -w /root mainnet-container bash".split())
    else:
        cmd = "docker exec --interactive mainnet-container goal".split()
        cmd.extend(goal_args)
        result = proc.run(
            cmd,
            stdout_log_level=logging.INFO,
            prefix_process=False,
            pass_stdin=True,
        )
    if result.exit_code != 0:
        sandbox = ComposeSandbox()
        ps_result = sandbox.ps("mainnet-container")
        match ps_result:
            case [{"State": "running"}]:
                pass  # container is running, failure must have been with command
            case _:
                logger.warning(
                    "mainnet-container does not appear to be running, "
                    "ensure mainnet node is started by executing `algorun start`"
                )
        raise click.exceptions.Exit(result.exit_code)  # pass on the exit code
