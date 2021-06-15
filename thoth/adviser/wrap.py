#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 - 2021 Fridolin Pokorny
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

"""A base class for implementing wrap units."""

import abc

import attr

from .state import State
from .unit import Unit


@attr.s(slots=True)
class Wrap(Unit):
    """Wrap base class implementation."""

    @staticmethod
    def is_wrap_unit_type() -> bool:
        """Check if this unit is of type wrap."""
        return True

    @abc.abstractmethod
    def run(self, state: State) -> None:
        """Run main entry-point for wrap units to filter and score packages."""
