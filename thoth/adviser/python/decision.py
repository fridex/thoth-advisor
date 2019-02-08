#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2018, 2019 Fridolin Pokorny
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

"""Decisison functions available for dependency monkey."""

import random
import typing

import attr

from thoth.storages import GraphDatabase
from thoth.adviser.config import ConfigEntry
from thoth.adviser.exceptions import InternalError


@attr.s(slots=True)
class DecisionFunction:
    """Decide which stacks should be executed in a dependency monkey run."""

    graph = attr.ib(type=GraphDatabase)
    configuration = attr.ib(type=ConfigEntry)

    @staticmethod
    def random_uniform(_: typing.List[tuple]):
        """Retrieve a random stack."""
        return random.getrandbits(1), []

    @staticmethod
    def everything(_: typing.List[tuple]):
        """Decide to include everything."""
        return 1.0, []

    @classmethod
    def get_decision_function(
        cls,
        graph: GraphDatabase,
        decision_function_name: str,
        configuration: ConfigEntry,
    ) -> typing.Callable:
        """Get decision function based on its name - return a bound method to self instance."""
        instance = cls(graph=graph, configuration=configuration)

        if decision_function_name == "random":
            return instance.random_uniform
        elif decision_function_name == "all":
            return instance.everything

        raise InternalError(
            f"Unknown decision function requested to be used - {decision_function_name}"
        )


DECISISON_FUNCTIONS = frozenset(("random", "all"))
DEFAULT_DECISION_FUNCTION = "all"
