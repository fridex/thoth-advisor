#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2021 Fridolin Pokorny
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

"""A base class for implementing package pseudonyms."""

import abc
import logging
from typing import Any
from typing import Dict
from typing import Tuple
from typing import Generator
from typing import Optional
from typing import TYPE_CHECKING

from thoth.python import PackageVersion
from voluptuous import Schema
from voluptuous import Required
import attr

from packaging.specifiers import SpecifierSet
from .unit import UnitPrescription

if TYPE_CHECKING:
    from ...pipeline_builder import PipelineBuilderContext

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class PseudonymPrescription(UnitPrescription):
    """Pseudonym base class implementation."""

    # Pseudonym is always specific to a package.
    CONFIGURATION_SCHEMA: Schema = Schema({Required("package_name"): str})

    _specifier = attr.ib(type=Optional[SpecifierSet], kw_only=True, init=False, default=None)
    _index_url = attr.ib(type=Optional[str], kw_only=True, init=False, default=None)

    @staticmethod
    def is_pseudonym_unit_type() -> bool:
        """Check if this unit is of type pseudonym."""
        return True

    @classmethod
    def should_include(cls, builder_context: "PipelineBuilderContext") -> Generator[Dict[str, Any], None, None]:
        """Check if the given pipeline unit should be included in the given pipeline configuration."""
        if cls._should_include_base(builder_context):
            prescription_run: Dict[str, Any] = cls._PRESCRIPTION["run"]  # type: ignore
            yield {"package_version": prescription_run["match"]["package_version"]["name"]}
            return None

        yield from ()
        return None

    def pre_run(self) -> None:
        """Prepare before running this pipeline unit."""
        version_specifier = self.run_prescription["match"]["package_version"].get("version")
        if version_specifier:
            self._specifier = SpecifierSet(version_specifier)

        self._index_url = self.run_prescription["match"]["package_version"].get("index_url")

    @abc.abstractmethod
    def run(self, package_version: PackageVersion) -> Generator[Tuple[str, str, str], None, None]:
        """Run main entry-point for pseudonyms to map packages to their counterparts."""
        if (self._index_url and package_version.index.url != self._index_url) or (
            self._specifier is not None and package_version.locked_version not in self._specifier
        ):
            yield from ()
            return None

        runtime_environment = self.context.project.runtime_environment
        pseudonyms = self.context.graph.get_solved_python_package_versions_all(
            package_name=self.run_prescription["yield"].get("package_version", {}).get("name"),
            package_version=self.run_prescription["yield"].get("package_version", {}).get("locked_version"),
            index_url=self.run_prescription["yield"].get("package_version", {}).get("index_url"),
            count=None,
            os_name=runtime_environment.operating_system.name,
            os_version=runtime_environment.operating_system.version,
            python_version=runtime_environment.python_version,
            distinct=True,
            is_missing=False,
        )

        for pseudonym in pseudonyms:
            _LOGGER.info(
                "%s: Considering package %r as a pseudonym of %r",
                self.get_unit_name(),
                pseudonym,
                package_version.to_tuple(),
            )
            yield pseudonym[0], pseudonym[1], pseudonym[2]
