#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019-2021 Fridolin Pokorny
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

"""Implementation of sieves used in adviser pipeline."""

from .constraints import ConstraintsSieve
from .experimental_filter_conf_index import FilterConfiguredIndexSieve
from .experimental_package_index import PackageIndexConfigurationSieve
from .experimental_prereleases import SelectiveCutPreReleasesSieve
from .filter_index import FilterIndexSieve
from .index_enabled import PackageIndexSieve
from .legacy_version import LegacyVersionSieve
from .locked import CutLockedSieve
from .prereleases import CutPreReleasesSieve
from .rules import SolverRulesSieve
from .solved import SolvedSieve
from .tensorflow import TensorFlow240AVX2IllegalInstructionSieve
from .tensorflow import TensorFlowAPISieve
from .tensorflow import TensorFlowCUDASieve
from .thoth_s2i_abi_compat import ThothS2IAbiCompatibilitySieve
from .thoth_s2i_packages import ThothS2IPackagesSieve
from .update import PackageUpdateSieve
from .version_constraint import VersionConstraintSieve

# Relative ordering of units is relevant, as the order specifies order
# in which the asked to be registered - any dependencies between them
# can be mentioned here.
__all__ = [
    "PackageUpdateSieve",
    "LegacyVersionSieve",
    "CutPreReleasesSieve",
    "ConstraintsSieve",
    "SelectiveCutPreReleasesSieve",
    "FilterConfiguredIndexSieve",
    "PackageIndexConfigurationSieve",
    "CutLockedSieve",
    "PackageIndexSieve",
    "SolvedSieve",
    "SolverRulesSieve",
    "VersionConstraintSieve",
    "ThothS2IPackagesSieve",
    "ThothS2IAbiCompatibilitySieve",
    "FilterIndexSieve",
    "TensorFlow240AVX2IllegalInstructionSieve",
    "TensorFlowAPISieve",
    "TensorFlowCUDASieve",
]
