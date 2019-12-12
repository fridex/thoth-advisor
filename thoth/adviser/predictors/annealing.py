#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 Fridolin Pokorny
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

"""Implementation of Adaptive Simulated Annealing (ASA) used to resolve software stacks."""

from typing import Any
from typing import Tuple
from typing import List
from typing import Optional
import logging
from math import exp
import random

import attr
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from ..beam import Beam
from ..context import Context
from ..enums import RecommendationType
from ..exceptions import NoHistoryKept
from ..predictor import Predictor
from ..state import State


_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class AdaptiveSimulatedAnnealing(Predictor):
    """Implementation of adaptive simulated annealing looking for stacks based on the scoring function."""

    _temperature_history = attr.ib(
        type=List[Tuple[float, bool, float, int]],
        default=attr.Factory(list),
        kw_only=True,
    )
    _temperature = attr.ib(type=float, kw_only=True, default=0.0)

    @staticmethod
    def _exp(iteration: int, t0: float, count: int, limit: int) -> float:
        """Exponential temperature function.

        See also:
             https://www.mathworks.com/help/gads/how-simulated-annealing-works.html
        """
        k = count / limit
        temperature = t0 * (0.95 ** k)
        _LOGGER.debug(
            "New temperature for (iteration=%d, t0=%g, count=%d, limit=%d, k=%f) = %g",
            iteration,
            t0,
            count,
            limit,
            k,
            temperature,
        )
        return temperature

    @staticmethod
    def _compute_acceptance_probability(
        top_score: float, neighbour_score: float, temperature: float
    ) -> float:
        """Check the probability of acceptance the given solution to expansion."""
        if neighbour_score > top_score:
            return 1.0

        # This should never occur based on resolver logic, but just to be sure...
        if temperature <= 0.0:
            _LOGGER.error("Temperature dropped to %g: temperature should be a positive number")
            return 0.0

        acceptance_probability = exp((neighbour_score - top_score) / temperature)
        _LOGGER.debug(
            "Acceptance probability for (top_score=%g, neighbour_score=%g, temperature=%g) = %g",
            top_score,
            neighbour_score,
            temperature,
            acceptance_probability,
        )
        return acceptance_probability

    def run(self, context: Context, beam: Beam) -> State:
        """Run adaptive simulated annealing on top of beam."""
        if context.recommendation_type == RecommendationType.LATEST:
            # If we have latest recommendations, try to expand the most recent version, always.
            _LOGGER.debug("Expanding the first state (hill climbing)")
            return beam.get(0)

        self._temperature = self._exp(
            context.iteration,
            self._temperature,
            context.accepted_final_states_count,
            context.limit,
        )

        # Expand highest promising by default.
        to_expand_state = beam.top()

        # Pick a random state to be expanded if accepted.
        probable_state_idx = random.randrange(1, beam.size) if beam.size > 1 else 0
        probable_state = beam.get(probable_state_idx)
        acceptance_probability = self._compute_acceptance_probability(
            to_expand_state.score, probable_state.score, self._temperature
        )

        if probable_state_idx != 0 and acceptance_probability >= random.uniform(
            0.0, 1.0
        ):
            # Skip to probable state, do not use the top rated state.
            _LOGGER.debug(
                "Performing transition to neighbour state with score %g",
                probable_state.score,
            )
            # state_expansion_idx = probable_state_idx
            to_expand_state = probable_state
        else:
            _LOGGER.debug(
                "Expanding TOP rated state with score %g", to_expand_state.score
            )

        if self.keep_history:
            self._temperature_history.append(
                (
                    self._temperature,
                    to_expand_state is beam.top(),
                    acceptance_probability,
                    context.accepted_final_states_count,
                )
            )

        return to_expand_state

    def pre_run(self, context: Context) -> None:
        """Initialization before the actual annealing run."""
        self._temperature_history = []
        self._temperature = context.limit

    @staticmethod
    def _make_patch_spines_invisible(ax: Any) -> None:
        """Make spines invisible."""
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        for sp in ax.spines.values():
            sp.set_visible(False)

    def plot(self) -> matplotlib.figure.Figure:
        """Plot temperature history of adaptive simulated annealing."""
        # Code adjusted based on:
        #    https://matplotlib.org/3.1.1/gallery/ticks_and_spines/multiple_yaxis_with_spines.html

        if self._temperature_history is None:
            raise NoHistoryKept("No history datapoints kept")

        x = [i for i in range(len(self._temperature_history))]
        # Top rated candidate was chosen.
        y1 = [i[0] if i[1] is True else None for i in self._temperature_history]
        # A neighbour candidate was chosen.
        y2 = [i[0] if i[1] is False else None for i in self._temperature_history]
        # Acceptance probability - as the probability in 0 - 1, lets make it larger - scale to temperature size.
        y3 = [i[2] for i in self._temperature_history]
        # Number of products.
        y4 = [i[3] for i in self._temperature_history]

        fig, host = plt.subplots()
        fig.subplots_adjust(right=0.75)

        par1 = host.twinx()
        par2 = host.twinx()

        # Offset the right spine of par1 and par2. The ticks and label have already been
        # placed on the right by twinx above.
        par1.spines["right"].set_position(("axes", 1.050))
        par2.spines["right"].set_position(("axes", 1.225))

        # Having been created by twinx, par1 par2 have their frame off, so the line of its
        # detached spine is invisible. First, activate the frame but make the patch
        # and spines invisible.
        self._make_patch_spines_invisible(par1)
        self._make_patch_spines_invisible(par2)

        # Second, show the right spine.
        par1.spines["right"].set_visible(True)
        par2.spines["right"].set_visible(True)
        host.spines["right"].set_visible(False)
        host.spines["top"].set_visible(False)

        p1, = host.plot(x, y1, ".g", label="Expansion of a highest rated candidate")
        host.plot(x, y2, ",r", label="Expansion of a neighbour candidate")
        p3, = par1.plot(
            x, y3, ",b", label="Acceptance probability for a neighbour candidate"
        )
        p4, = par2.plot(
            x, y4, ",y", label="Number of products produced in the pipeline"
        )

        host.set_xlabel("iteration")
        host.set_ylabel("temperature")
        par1.set_ylabel("acceptance probability")
        par2.set_ylabel("product count")

        host.yaxis.label.set_color("black")
        par1.yaxis.label.set_color(p3.get_color())
        par2.yaxis.label.set_color(p4.get_color())

        tkw = dict(size=4, width=1.5)
        host.tick_params(axis="y", colors="black", **tkw)
        par1.tick_params(axis="y", colors=p3.get_color(), **tkw)
        par2.tick_params(axis="y", colors=p4.get_color(), **tkw)
        host.tick_params(axis="x", **tkw)

        font_prop = FontProperties()
        font_prop.set_size("small")
        fig.legend(
            loc="upper center",
            bbox_to_anchor=(0.50, 1.00),
            ncol=2,
            fancybox=True,
            shadow=True,
            prop=font_prop,
        )
        return fig
