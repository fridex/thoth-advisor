#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018 Fridolin Pokorny
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Thoth-adviser CLI."""

import json
import logging
import typing
from copy import deepcopy

import click
from thoth.adviser import __title__ as analyzer_name
from thoth.adviser import __version__ as analyzer_version
from thoth.adviser.enums import PythonRecommendationOutput
from thoth.adviser.enums import RecommendationType
from thoth.adviser.exceptions import InternalError
from thoth.adviser.exceptions import ThothAdviserException
from thoth.adviser.python import Adviser
from thoth.adviser.python import DECISISON_FUNCTIONS
from thoth.adviser.python import GraphDigestsFetcher
from thoth.adviser.python import dependency_monkey as run_dependency_monkey
from thoth.adviser.python.dependency_monkey import dm_amun_inspect_wrapper
from thoth.adviser.runtime_environment import RuntimeEnvironment
from thoth.analyzer import print_command_result
from thoth.common import init_logging
from thoth.python import Pipfile
from thoth.python import PipfileLock
from thoth.python import Project
from thoth.solver.python.base import SolverException

init_logging()

_LOGGER = logging.getLogger(__name__)


def _print_version(ctx, _, value):
    """Print adviser version and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(analyzer_version)
    ctx.exit()


def _instantiate_project(
    requirements: str, requirements_locked: typing.Optional[str], files: bool
):
    """Create Project instance based on arguments passed to CLI."""
    if files:
        with open(requirements, "r") as requirements_file:
            requirements = requirements_file.read()

        if requirements_locked:
            with open(requirements_locked, "r") as requirements_file:
                requirements_locked = requirements_file.read()
            del requirements_file
    else:
        # We we gather values from env vars, un-escape new lines.
        requirements = requirements.replace("\\n", "\n")
        if requirements_locked:
            requirements_locked = requirements_locked.replace("\\n", "\n")

    pipfile = Pipfile.from_string(requirements)
    pipfile_lock = (
        PipfileLock.from_string(requirements_locked, pipfile)
        if requirements_locked
        else None
    )
    project = Project(pipfile=pipfile, pipfile_lock=pipfile_lock)

    return project


@click.group()
@click.pass_context
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    envvar="THOTH_ADVISER_DEBUG",
    help="Be verbose about what's going on.",
)
@click.option(
    "--version",
    is_flag=True,
    is_eager=True,
    callback=_print_version,
    expose_value=False,
    help="Print adviser version and exit.",
)
def cli(ctx=None, verbose=False):
    """Thoth adviser command line interface."""
    if ctx:
        ctx.auto_envvar_prefix = "THOTH_ADVISER"

    if verbose:
        _LOGGER.setLevel(logging.DEBUG)

    _LOGGER.debug("Debug mode is on")


@cli.command()
@click.pass_context
@click.option(
    "--requirements",
    "-r",
    type=str,
    envvar="THOTH_ADVISER_REQUIREMENTS",
    required=True,
    help="Pipfile to be checked for provenance.",
)
@click.option(
    "--requirements-locked",
    "-l",
    type=str,
    envvar="THOTH_ADVISER_REQUIREMENTS_LOCKED",
    required=True,
    help="Pipenv.lock file stating currently locked packages.",
)
@click.option(
    "--output",
    "-o",
    type=str,
    envvar="THOTH_ADVISER_OUTPUT",
    default="-",
    help="Output file or remote API to print results to, in case of URL a POST request is issued.",
)
@click.option("--no-pretty", "-P", is_flag=True, help="Do not print results nicely.")
@click.option(
    "--whitelisted-sources",
    "-i",
    type=str,
    required=False,
    envvar="THOTH_WHITELISTED_SOURCES",
    help="A comma separated list of whitelisted simple repositories providing packages - if not "
    "provided, all indexes are whitelisted (example: https://pypi.org/simple/).",
)
@click.option(
    "--files",
    "-F",
    is_flag=True,
    help="Requirements passed represent paths to files on local filesystem.",
)
def provenance(
    click_ctx,
    requirements,
    requirements_locked=None,
    whitelisted_sources=None,
    output=None,
    files=False,
    no_pretty=False,
):
    """Check provenance of packages based on configuration."""
    _LOGGER.debug("Passed arguments: %s", locals())

    whitelisted_sources = whitelisted_sources.split(",") if whitelisted_sources else []
    result = {
        "error": None,
        "report": [],
        "parameters": {"whitelisted_indexes": whitelisted_sources},
        "input": None,
    }
    try:
        project = _instantiate_project(requirements, requirements_locked, files)
        result["input"] = project.to_dict()
        report = project.check_provenance(
            whitelisted_sources=whitelisted_sources,
            digests_fetcher=GraphDigestsFetcher(),
        )
    except ThothAdviserException as exc:
        # TODO: we should extend exceptions so they are capable of storing more info.
        if isinstance(exc, InternalError):
            # Re-raise internal exceptions that shouldn't occur here.
            raise

        _LOGGER.exception("Error during checking provenance: %s", str(exc))
        result["error"] = True
        result["report"] = [
            {"type": "ERROR", "justification": f"{str(exc)} ({type(exc).__name__})"}
        ]
    else:
        result["error"] = False
        result["report"] = report

    print_command_result(
        click_ctx,
        result,
        analyzer=analyzer_name,
        analyzer_version=analyzer_version,
        output=output,
        pretty=not no_pretty,
    )
    return int(result["error"] is True)


@cli.command()
@click.pass_context
@click.option(
    "--requirements",
    "-r",
    type=str,
    envvar="THOTH_ADVISER_REQUIREMENTS",
    required=True,
    help="Requirements to be advised.",
)
@click.option(
    "--requirements-locked",
    "-l",
    type=str,
    envvar="THOTH_ADVISER_REQUIREMENTS_LOCKED",
    help="Currently locked down requirements used.",
)
@click.option(
    "--requirements-format",
    "-f",
    envvar="THOTH_REQUIREMENTS_FORMAT",
    default="pipenv",
    required=True,
    type=click.Choice(["pipenv", "requirements"]),
    help="The output format of requirements that are computed based on recommendations.",
)
@click.option(
    "--output",
    "-o",
    type=str,
    envvar="THOTH_ADVISER_OUTPUT",
    default="-",
    help="Output file or remote API to print results to, in case of URL a POST request is issued.",
)
@click.option("--no-pretty", "-P", is_flag=True, help="Do not print results nicely.")
@click.option(
    "--recommendation-type",
    "-t",
    envvar="THOTH_ADVISER_RECOMMENDATION_TYPE",
    default="stable",
    required=True,
    type=click.Choice(["stable", "testing", "latest"]),
    help="Type of recommendation generated based on knowledge base.",
)
@click.option(
    "--count",
    envvar="THOTH_ADVISER_COUNT",
    help="Number of software stacks that should be taken into account in the output.",
)
@click.option(
    "--limit",
    envvar="THOTH_ADVISER_LIMIT",
    help="Number of software stacks that should be taken into account in the output.",
)
@click.option(
    "--runtime-environment",
    "-e",
    envvar="THOTH_ADVISER_RUNTIME_ENVIRONMENT",
    type=str,
    help="Type of recommendation generated based on knowledge base.",
)
@click.option(
    "--files",
    "-F",
    is_flag=True,
    help="Requirements passed represent paths to files on local filesystem.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Do not output generated stacks, output just stack count.",
)
def advise(
    click_ctx,
    requirements,
    requirements_format=None,
    requirements_locked=None,
    recommendation_type=None,
    runtime_environment=None,
    output=None,
    no_pretty=False,
    files=False,
    count=None,
    limit=None,
    dry_run=False,
):
    """Advise package and package versions in the given stack or on solely package only."""
    _LOGGER.debug("Passed arguments: %s", locals())
    limit = int(limit) if limit else None
    count = int(count) if count else None

    if runtime_environment:
        runtime_environment = json.loads(runtime_environment)
    else:
        runtime_environment = {}

    recommendation_type = RecommendationType.by_name(recommendation_type)
    requirements_format = PythonRecommendationOutput.by_name(requirements_format)
    result = {
        "error": None,
        "report": [],
        "parameters": {
            "runtime_environment": runtime_environment,
            "recommendation_type": recommendation_type.name.lower(),
            "requirements_format": requirements_format.name.lower(),
            "limit": limit,
            "count": count,
            "dry_run": dry_run,
            "no_pretty": no_pretty,
        },
        "input": None,
    }

    runtime_environment = RuntimeEnvironment.from_dict(runtime_environment)

    try:
        project = _instantiate_project(requirements, requirements_locked, files)
        result["input"] = project.to_dict()
        report = Adviser.compute_on_project(
            project,
            runtime_environment=runtime_environment,
            recommendation_type=recommendation_type,
            count=count,
            limit=limit,
            dry_run=dry_run,
        )
    except ThothAdviserException as exc:
        # TODO: we should extend exceptions so they are capable of storing more info.
        if isinstance(exc, InternalError):
            # Re-raise internal exceptions that shouldn't occur here.
            raise

        _LOGGER.exception("Error during computing recommendation: %s", str(exc))
        result["error"] = True
        result["report"] = [([{"justification": f"{str(exc)}", "type": "ERROR"}], None)]
    except SolverException as exc:
        result["error"] = True
        result["report"] = [([{"justification": str(exc), "type": "ERROR"}], None)]
    else:
        result["error"] = False
        # Convert report to a dict so its serialized.
        if not dry_run:
            result["report"] = [(item[0], item[1].to_dict()) for item in report]
        else:
            result["report"] = report

    print_command_result(
        click_ctx,
        result,
        analyzer=analyzer_name,
        analyzer_version=analyzer_version,
        output=output,
        pretty=not no_pretty,
    )
    return int(result["error"] is True)


@cli.command("dependency-monkey")
@click.pass_context
@click.option(
    "--requirements",
    "-r",
    type=str,
    envvar="THOTH_ADVISER_REQUIREMENTS",
    required=True,
    help="Requirements to be advised.",
)
@click.option(
    "--stack-output",
    "-o",
    type=str,
    envvar="THOTH_DEPENDENCY_MONKEY_STACK_OUTPUT",
    required=True,
    help="Output directory or remote API to print results to, in case of URL a POST request "
    "is issued to the Amun REST API.",
)
@click.option(
    "--report-output",
    "-R",
    type=str,
    envvar="THOTH_DEPENDENCY_MONKEY_REPORT_OUTPUT",
    required=False,
    default="-",
    help="Output directory or remote API where reports of dependency monkey run should be posted..",
)
@click.option(
    "--files",
    "-F",
    is_flag=True,
    help="Requirements passed represent paths to files on local filesystem.",
)
@click.option(
    "--seed",
    envvar="THOTH_DEPENDENCY_MONKEY_SEED",
    help="A seed to be used for generating software stack samples (defaults to time if omitted).",
)
@click.option(
    "--count",
    envvar="THOTH_DEPENDENCY_MONKEY_COUNT",
    help="Number of software stacks that should be computed.",
)
@click.option(
    "--decision",
    required=False,
    envvar="THOTH_DEPENDENCY_MONKEY_DECISION",
    default="all",
    type=click.Choice(DECISISON_FUNCTIONS),
    help="A decision function that should be used for generating software stack samples; "
    "if omitted, all software stacks will be created.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    envvar="THOTH_DEPENDENCY_MONKEY_DRY_RUN",
    help="Do not generate software stacks, just report how many software stacks will be "
    "generated given the provided configuration.",
)
@click.option(
    "--context",
    type=str,
    envvar="THOTH_AMUN_CONTEXT",
    help="The context into which computed stacks should be placed; if omitteed, "
    "raw software stacks will be created. This option cannot be set when generating "
    "software stacks onto filesystem.",
)
@click.option(
    "--runtime-environment",
    "-e",
    envvar="THOTH_ADVISER_RUNTIME_ENVIRONMENT",
    type=str,
    help="Runtime environment that is used for verifying stacks.",
)
@click.option("--no-pretty", "-P", is_flag=True, help="Do not print results nicely.")
def dependency_monkey(
    click_ctx,
    requirements: str,
    stack_output: str,
    report_output: str,
    files: bool,
    seed: int = None,
    decision: str = None,
    dry_run: bool = False,
    context: str = None,
    no_pretty: bool = False,
    count: int = None,
    runtime_environment: dict = None,
):
    """Generate software stacks based on all valid resolutions that conform version ranges."""
    project = _instantiate_project(requirements, requirements_locked=None, files=files)

    # We cannot have these as ints in click because they are optional and we
    # cannot pass empty string as an int as env variable.
    seed = int(seed) if seed else None
    count = int(count) if count else None

    if runtime_environment:
        runtime_environment = json.loads(runtime_environment)
    else:
        runtime_environment = {}

    result = {
        "error": False,
        "parameters": {
            "requirements": project.pipfile.to_dict(),
            "runtime_environment": runtime_environment,
            "seed": seed,
            "decision": decision,
            "context": deepcopy(
                context
            ),  # We reuse context later, perform deepcopy to report the one on input.
            "stack_output": stack_output,
            "report_output": report_output,
            "files": files,
            "dry_run": dry_run,
            "no_pretty": no_pretty,
            "count": count,
        },
        "input": None,
        "output": [],
        "computed": None,
    }

    runtime_environment = RuntimeEnvironment.from_dict(runtime_environment)

    try:
        report = run_dependency_monkey(
            project,
            stack_output,
            seed=seed,
            decision_function_name=decision,
            dry_run=dry_run,
            context=context,
            count=count,
            runtime_environment=runtime_environment,
        )
        # Place report into result.
        result.update(report)
    except SolverException:
        result["error"] = True

    print_command_result(
        click_ctx,
        result,
        analyzer=analyzer_name,
        analyzer_version=analyzer_version,
        output=report_output,
        pretty=not no_pretty,
    )

    return int(result["error"] is True)


@cli.command("submit-amun")
@click.option(
    "--requirements",
    "-r",
    type=str,
    envvar="THOTH_ADVISER_REQUIREMENTS",
    required=True,
    help="Requirements to be advised.",
)
@click.option(
    "--requirements-locked",
    "-r",
    type=str,
    envvar="THOTH_ADVISER_REQUIREMENTS",
    required=True,
    help="Requirements to be advised.",
)
@click.option(
    "--stack-output",
    "-o",
    type=str,
    envvar="THOTH_DEPENDENCY_MONKEY_STACK_OUTPUT",
    required=True,
    help="Output directory or remote API to print results to, in case of URL a POST request "
    "is issued to the Amun REST API.",
)
@click.option(
    "--files",
    "-F",
    is_flag=True,
    help="Requirements passed represent paths to files on local filesystem.",
)
@click.option(
    "--context",
    type=str,
    envvar="THOTH_AMUN_CONTEXT",
    help="The context into which computed stacks should be placed; if omitteed, "
    "raw software stacks will be created. This option cannot be set when generating "
    "software stacks onto filesystem.",
)
def submit_amun(
    requirements: str,
    requirements_locked: str,
    stack_output: str,
    files: bool,
    context: str = None,
):
    """Submit the given project to Amun for inspection - mostly for debug purposes."""
    project = _instantiate_project(
        requirements, requirements_locked=requirements_locked, files=files
    )
    context = json.loads(context) if context else {}
    inspection_id = dm_amun_inspect_wrapper(stack_output, context, project, 0)
    print(inspection_id)


if __name__ == "__main__":
    cli()
