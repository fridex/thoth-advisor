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

"""Implementation of a prescription abstraction."""

import logging
import os
import yaml
from collections import OrderedDict
from typing import Any
from typing import Dict
from typing import Generator

import attr

from ...exceptions import PrescriptionSchemaError
from .schema import PRESCRIPTION_SCHEMA
from .boot import BootPrescription
from .pseudonym import PseudonymPrescription
from .sieve import SievePrescription
from .step import StepPrescription
from .stride import StridePrescription
from .wrap import WrapPrescription

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Prescription:
    """Dynamically create pipeline units based on inscription."""

    _VALIDATE_PRESCRIPTION_SCHEMA = bool(int(os.getenv("THOTH_VALIDATE_PRESCRIPTION_SCHEMA", 1)))

    boots_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    pseudonyms_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    sieves_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    steps_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    strides_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))
    wraps_dict = attr.ib(type=Dict[str, Dict[str, Any]], kw_only=True, default=attr.Factory(OrderedDict))

    @classmethod
    def from_dict(cls, prescription: Dict[str, Any]) -> "Prescription":
        """Instantiate prescription from a dictionary representation."""
        if cls._VALIDATE_PRESCRIPTION_SCHEMA:
            _LOGGER.debug("Validating prescription schema")
            try:
                PRESCRIPTION_SCHEMA(prescription)
            except Exception as exc:
                _LOGGER.exception(
                    "Failed to validate schema for prescription: %s",
                    str(exc),
                )
                raise PrescriptionSchemaError(str(exc))

        boots_dict = OrderedDict()
        for boot_spec in prescription["spec"]["units"].get("boots") or []:
            boot_spec["name"] = f"prescription.{boot_spec['name']}"
            boots_dict[boot_spec["name"]] = boot_spec

        pseudonyms_dict = OrderedDict()
        for pseudonym_spec in prescription["spec"]["units"].get("pseudonyms") or []:
            pseudonym_spec["name"] = f"prescription.{pseudonym_spec['name']}"
            pseudonyms_dict[pseudonym_spec["name"]] = pseudonym_spec

        sieves_dict = OrderedDict()
        for sieve_spec in prescription["spec"]["units"].get("sieves") or []:
            sieve_spec["name"] = f"prescription.{sieve_spec['name']}"
            sieves_dict[sieve_spec["name"]] = sieve_spec

        steps_dict = OrderedDict()
        for step_spec in prescription["spec"]["units"].get("steps") or []:
            step_spec["name"] = f"prescription.{step_spec['name']}"
            steps_dict[step_spec["name"]] = step_spec

        strides_dict = OrderedDict()
        for stride_spec in prescription["spec"]["units"].get("strides") or []:
            stride_spec["name"] = f"prescription.{stride_spec['name']}"
            strides_dict[stride_spec["name"]] = stride_spec

        wraps_dict = OrderedDict()
        for wrap_spec in prescription["spec"]["units"].get("strides") or []:
            wrap_spec["name"] = f"prescription.{wrap_spec['name']}"
            wraps_dict[wrap_spec["name"]] = wrap_spec

        return cls(
            boots_dict=boots_dict,
            pseudonyms_dict=pseudonyms_dict,
            sieves_dict=sieves_dict,
            steps_dict=steps_dict,
            strides_dict=strides_dict,
            wraps_dict=wraps_dict,
        )

    @classmethod
    def load(cls, prescription: str) -> "Prescription":
        """Load prescription from a string or file."""
        if os.path.isfile(prescription):
            _LOGGER.debug("Loading prescription from file %r", prescription)
            with open(prescription, "r") as config_file:
                prescription = config_file.read()

        return cls.from_dict(yaml.safe_load(prescription))

    @staticmethod
    def _iter_units(unit_class: type, units: Dict[str, Any]) -> Generator[type, None, None]:
        """Iterate over units registered."""
        for prescription in units.values():
            unit_class.set_prescription(prescription)  # type: ignore

            yield unit_class

    def iter_boot_units(self) -> Generator[type, None, None]:
        """Iterate over prescription boot units registered in the prescription supplied."""
        return self._iter_units(BootPrescription, self.boots_dict)

    def iter_pseudonym_units(self) -> Generator[type, None, None]:
        """Iterate over prescription pseudonym units registered in the prescription supplied."""
        return self._iter_units(PseudonymPrescription, self.pseudonyms_dict)

    def iter_sieve_units(self) -> Generator[type, None, None]:
        """Iterate over prescription sieve units registered in the prescription supplied."""
        return self._iter_units(SievePrescription, self.sieves_dict)

    def iter_step_units(self) -> Generator[type, None, None]:
        """Iterate over prescription step units registered in the prescription supplied."""
        return self._iter_units(StepPrescription, self.steps_dict)

    def iter_stride_units(self) -> Generator[type, None, None]:
        """Iterate over prescription stride units registered in the prescription supplied."""
        return self._iter_units(StridePrescription, self.strides_dict)

    def iter_wrap_units(self) -> Generator[type, None, None]:
        """Iterate over prescription stride units registered in the prescription supplied."""
        return self._iter_units(WrapPrescription, self.wraps_dict)
