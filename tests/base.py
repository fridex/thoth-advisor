#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

"""A base class for implementing adviser's test cases."""

from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
import os

from voluptuous import All
from voluptuous import Any as SchemaAny
from voluptuous import Optional as SchemaOptional
from voluptuous import Invalid
from voluptuous import Length
from voluptuous import Schema

from thoth.adviser.pipeline_builder import PipelineBuilderContext


class AdviserTestCaseException(Exception):
    """A base class for exceptions that can occur in the test suite."""


class AdviserJustificationSchemaError(AdviserTestCaseException):
    """An exception raised when the justification reported violates schema."""


class AdviserTestCase:
    """A base class for implementing adviser's test cases."""

    data_dir = Path(os.path.dirname(os.path.realpath(__file__))) / "data"

    JUSTIFICATION_SAMPLE_1 = [
        {"message": "Justification sample 1", "type": "WARNING", "link": "https://thoth-station.ninja"},
        {"message": "Justification sample 1", "type": "INFO", "link": "https://thoth-station.ninja"},
        {"message": "Justification sample 1", "type": "ERROR", "link": "https://thoth-station.ninja"},
    ]

    JUSTIFICATION_SAMPLE_2 = [
        {
            "message": "Justification sample 2",
            "type": "INFO",
            "link": "https://thoth-station.ninja",
            "advisory": "Bark!",
        },
    ]

    JUSTIFICATION_SAMPLE_3 = [
        {
            "message": "Justification sample 2",
            "type": "INFO",
            "link": "https://thoth-station.ninja",
            "package_name": "tensorflow",
            "version_range": "<2.3>=",
        },
    ]

    _JUSTIFICATION_SCHEMA = Schema(
        [
            {
                "message": All(str, Length(min=1)),
                "type": SchemaAny("INFO", "WARNING", "ERROR", "LATEST", "CVE"),
                "link": All(str, Length(min=1)),
                SchemaOptional("advisory"): All(str, Length(min=1)),
                SchemaOptional("cve_id"): All(str, Length(min=1)),
                SchemaOptional("cve_name"): All(str, Length(min=1)),
                SchemaOptional("package_name"): All(str, Length(min=1)),
                SchemaOptional("version_range"): All(str, Length(min=1)),
            }
        ]
    )

    @classmethod
    def verify_justification_schema(cls, justification: Optional[List[Dict[str, Any]]]) -> bool:
        """Verify the justification schema is correct."""
        if justification is None:
            return True

        try:
            cls._JUSTIFICATION_SCHEMA(justification)
        except Invalid as exc:
            raise AdviserJustificationSchemaError(exc.msg) from exc
        else:
            return True


class AdviserUnitTestCase(AdviserTestCase):
    """A base class for implementing pipeline unit specific test cases."""

    UNIT_TESTED = None

    @classmethod
    def verify_multiple_should_include(cls, builder_context: PipelineBuilderContext) -> bool:
        """Check multiple should_include calls do not end in an infinite loop."""
        assert cls.UNIT_TESTED is not None, "No unit assigned for testing"
        pipeline_config = cls.UNIT_TESTED.should_include(builder_context)
        assert pipeline_config is not None, "First call to should_include should be always non-None"

        unit = cls.UNIT_TESTED()
        if pipeline_config:
            unit.update_configuration(pipeline_config)

        builder_context.add_unit(unit)
        assert (
            cls.UNIT_TESTED.should_include(builder_context) is None
        ), "Make sure the pipeline unit does not loop endlessly on multiple should_include calls"
        return True

    def test_verify_multiple_should_include(self, *args, **kwargs) -> bool:
        """Check multiple should_include calls do not end in an infinite loop."""
        # Construct a builder context that should always include a pipeline unit and pass
        # it to verify_multiple_should_include
        raise NotImplementedError(
            "Implement a test that makes sure multiple calls of should include do not loop endlessly"
        )
