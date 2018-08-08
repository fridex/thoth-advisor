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

import sys

import click
import logging

from thoth.analyzer import print_command_result
from thoth.common import init_logging

from thoth.adviser.enums import PythonRecommendationOutput
from thoth.adviser.enums import RecommendationType
from thoth.adviser.exceptions import ThothAdviserException
from thoth.adviser.exceptions import InternalError
from thoth.adviser import __title__ as analyzer_name
from thoth.adviser import __version__ as analyzer_version
from thoth.adviser.python import Pipfile, PipfileLock
from thoth.adviser.python import Project

init_logging()

_LOGGER = logging.getLogger(__name__)


def _print_version(ctx, _, value):
    """Print adviser version and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(analyzer_version)
    ctx.exit()


@click.group()
@click.pass_context
@click.option('-v', '--verbose', is_flag=True, envvar='THOTH_ADVISER_DEBUG',
              help="Be verbose about what's going on.")
@click.option('--version', is_flag=True, is_eager=True, callback=_print_version, expose_value=False,
              help="Print adviser version and exit.")
def cli(ctx=None, verbose=False):
    """Thoth adviser command line interface."""
    if ctx:
        ctx.auto_envvar_prefix = 'THOTH_ADVISER'

    if verbose:
        _LOGGER.setLevel(logging.DEBUG)

    _LOGGER.debug("Debug mode is on")


@cli.command()
@click.pass_context
@click.option('--requirements', '-r', type=str, envvar='THOTH_ADVISER_REQUIREMENTS', required=True,
              help="Requirements to be advised.")
@click.option('--requirements-locked', '-l', type=str, envvar='THOTH_ADVISER_REQUIREMENTS_LOCKED',
              help="Currently locked down requirements used.")
@click.option('--requirements-format', '-f', envvar='THOTH_REQUIREMENTS_FORMAT', default='pipenv', required=True,
              type=click.Choice(['pipenv', 'requirements']),
              help="The output format of requirements that are computed based on recommendations.")
@click.option('--output', '-o', type=str, envvar='THOTH_ADVISER_OUTPUT', default='-',
              help="Output file or remote API to print results to, in case of URL a POST request is issued.")
@click.option('--no-pretty', '-P', is_flag=True,
              help="Do not print results nicely.")
@click.option('--recommendation-type', '-t', envvar='THOTH_ADVISER_RECOMMENDATION_TYPE', default='stable',
              required=True,
              type=click.Choice(['stable', 'testing', 'latest']),
              help="Type of recommendation generated based on knowledge base.")
@click.option('--runtime-environment', '-e', envvar='THOTH_ADVISER_RUNTIME_ENVIRONMENT', type=str,
              help="Type of recommendation generated based on knowledge base.")
@click.option('--files', '-F', is_flag=True,
              help="Requirements passed represent paths to files on local filesystem.")
def pypi(click_ctx, requirements, requirements_format=None, requirements_locked=None,
         recommendation_type=None, runtime_environment=None, output=None, no_pretty=False, files=False):
    """Advise package and package versions in the given stack or on solely package only."""
    _LOGGER.debug("Passed arguments: %s", locals())

    if not requirements:
        _LOGGER.error("No requirements specified, exiting")
        sys.exit(1)

    # TODO: we should handle exceptions here and report them back as errors a user can directly inspect/report.

    if files:
        with open(requirements, 'r') as requirements_file:
            requirements = requirements_file.read()

        if requirements_locked:
            with open(requirements_locked, 'r') as requirements_locked_file:
                requirements_locked = requirements_locked_file.read()
    else:
        # We we gather values from env vars, un-escape new lines.
        requirements = requirements.replace('\\n', '\n')
        if requirements_locked:
            requirements_locked = requirements_locked.replace('\\n', '\n')

    recommendation_type = RecommendationType.by_name(recommendation_type)
    requirements_format = PythonRecommendationOutput.by_name(requirements_format)
    result = {
        'error': None,
        'report': {},
        'parameters': {
            'runtime_environment': runtime_environment,
            'recommendation_type': recommendation_type.name.lower(),
            'requirements_format': requirements_format.name.lower()
        },
        'input': {
            'requirements': requirements,
            'requirements_locked': requirements_locked
        },
        'output': {
            'requirements': None,
            'requirements_locked': None
        }
    }
    try:
        pipfile = Pipfile.parse(requirements)
        pipfile_lock = None
        if requirements_locked:
            pipfile_lock = PipfileLock.parse(requirements_locked, pipfile)

        project = Project(pipfile=pipfile, pipfile_lock=pipfile_lock)
        report = project.advise(runtime_environment, recommendation_type)
    except ThothAdviserException as exc:
        # TODO: we should extend exceptions so they are capable of storing more info.
        if isinstance(exc, InternalError):
            # Re-raise internal exceptions that shouldn't occur here.
            raise

        result = {
            'error': True,
            'report': {
                'error_type': type(exc).__name__,
                'error': str(exc)
            }
        }
    else:
        result['error'] = False
        if report:
            # If we have something to suggest, add it to output field.
            # Do not replicate input to output without any reason.
            if requirements_format == PythonRecommendationOutput.PIPENV:
                output_requirements = project.pipfile.to_string()
                output_requirements_locked = project.pipfile_lock.to_string()
            else:
                output_requirements = project.pipfile.to_requirements_file()
                output_requirements_locked = project.pipfile_lock.to_requirements_file()

            result['report'] = report
            result['output']['requirements'] = output_requirements
            result['output']['requirements_locked'] = output_requirements_locked

    print_command_result(
        click_ctx,
        result,
        analyzer=analyzer_name,
        analyzer_version=analyzer_version,
        output=output,
        pretty=not no_pretty
    )


if __name__ == '__main__':
    cli()
