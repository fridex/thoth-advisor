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

"""Test implementation of wrap prescription v1."""

import flexmock
import pytest
import yaml

from thoth.adviser.context import Context
from thoth.adviser.state import State
from thoth.adviser.prescription.v1 import WrapPrescription
from thoth.adviser.prescription.v1.schema import PRESCRIPTION_WRAP_SCHEMA

from .base import AdviserUnitPrescriptionTestCase


class TestWrapPrescription(AdviserUnitPrescriptionTestCase):
    """Tests related to wrap prescription v1."""

    def test_run_stack_info(self, context: Context, state: State) -> None:
        """Check assigning stack info."""
        prescription_str = """
name: WrapUnit
type: wrap
should_include:
  times: 1
  adviser_pipeline: true
match:
 state:
    resolved_dependencies:
      - name: werkzeug
        version: "<=1.0.0"
        index_url: 'https://pypi.org/simple'
run:
  stack_info:
    - type: WARNING
      message: Some message
      link: https://pypi.org/project/werkzeug
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_WRAP_SCHEMA(prescription)
        WrapPrescription.set_prescription(prescription)
        state.add_resolved_dependency(("werkzeug", "0.5.0", "https://pypi.org/simple"))
        self.check_run_stack_info(context, WrapPrescription, state=state)

    @pytest.mark.parametrize("log_level", ["INFO", "ERROR", "WARNING"])
    def test_run_log(self, caplog, context: Context, state: State, log_level: str) -> None:
        """Check logging messages."""
        prescription_str = f"""
name: WrapUnit
type: wrap
should_include:
  times: 1
  adviser_pipeline: true
match:
 state:
    resolved_dependencies:
      - name: flask
run:
  log:
    message: Seen flask in one of the resolved stacks
    type: {log_level}
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_WRAP_SCHEMA(prescription)
        WrapPrescription.set_prescription(prescription)
        state.add_resolved_dependency(("flask", "0.12", "https://pypi.org/simple"))
        self.check_run_log(caplog, context, log_level, WrapPrescription, state=state)

    def test_run_eager_stop_pipeline(self, context: Context, state: State) -> None:
        """Check eager stop pipeline configuration."""
        prescription_str = """
name: WrapUnit
type: wrap
should_include:
  times: 1
  dependency_monkey_pipeline: true
match:
 state:
   resolved_dependencies:
    - name: flask
      version: ==0.12
    - name: werkzeug
      version: ==1.0.1
    - name: itsdangerous
      version: <1.0
run:
  eager_stop_pipeline: These three cannot occur together
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_WRAP_SCHEMA(prescription)
        WrapPrescription.set_prescription(prescription)
        state.add_resolved_dependency(("flask", "0.12.0", "https://pypi.org/simple"))
        state.add_resolved_dependency(("werkzeug", "1.0.1", "https://pypi.org/simple"))
        state.add_resolved_dependency(("itsdangerous", "0.5.1", "https://pypi.org/simple"))
        self.check_run_eager_stop_pipeline(context, WrapPrescription, state=state)

    def test_run_not_acceptable(self, context: Context, state: State) -> None:
        """Check raising not acceptable."""
        prescription_str = """
name: WrapUnit
type: wrap
should_include:
  times: 1
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      - name: flask
        version: "<=1.0.0,>=0.12"
        index_url: "https://pypi.org/simple"
      - name: connexion
        version: "==2.7.0"
        index_url: "https://pypi.org/simple"
run:
  not_acceptable: This is exception message reported
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_WRAP_SCHEMA(prescription)
        WrapPrescription.set_prescription(prescription)
        state.add_resolved_dependency(("flask", "0.12", "https://pypi.org/simple"))
        state.add_resolved_dependency(("connexion", "2.7.0", "https://pypi.org/simple"))
        self.check_run_not_acceptable(context, WrapPrescription, state=state)

    def test_run_no_match(self, context: Context, state: State) -> None:
        """Test running this pipeline unit without match."""
        prescription_str = """
name: WrapUnit
type: wrap
should_include:
  times: 1
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      - name: flask
        version: "<=1.0.0,>=0.12"
        index_url: "https://pypi.org/simple"
      - name: connexion
        version: "==2.7.0"
        index_url: "https://pypi.org/simple"
run:
  stack_info:
    - type: ERROR
      message: This message will not be shown
      link: https://pypi.org/project/connexion
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_WRAP_SCHEMA(prescription)
        WrapPrescription.set_prescription(prescription)
        state.add_resolved_dependency(("flask", "0.12", "https://pypi.org/simple"))
        state.add_resolved_dependency(("connexion", "2.0.0", "https://pypi.org/simple"))

        assert not context.stack_info

        unit = WrapPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state) is None

        assert not context.stack_info

    def test_run_justification(self, context: Context, state: State) -> None:
        """Test running this pipeline unit without match."""
        prescription_str = """
name: WrapUnit
type: wrap
should_include:
  times: 1
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      - name: flask
        version: "<=1.0.0,>=0.12"
        index_url: "https://pypi.org/simple"
      - name: connexion
        version: "==2.7.0"
        index_url: "https://pypi.org/simple"
run:
  justification:
    - type: ERROR
      message: This message will not be shown
      link: https://pypi.org/project/connexion
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_WRAP_SCHEMA(prescription)
        WrapPrescription.set_prescription(prescription)
        state.add_resolved_dependency(("flask", "0.12", "https://pypi.org/simple"))
        state.add_resolved_dependency(("connexion", "2.7.0", "https://pypi.org/simple"))

        state.justification.clear()

        unit = WrapPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state) is None

        assert state.justification == unit.run_prescription["justification"]

    def test_should_include(self) -> None:
        """Test including this pipeline unit."""
        prescription_str = """
name: WrapUnit
type: wrap
should_include:
  times: 1
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      - name: flask
        version: "<=1.0.0,>=0.12"
        index_url: "https://pypi.org/simple"
run:
  justification:
    - type: ERROR
      message: This message will not be shown
      link: https://pypi.org/project/connexion
"""
        flexmock(WrapPrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_WRAP_SCHEMA(prescription)
        WrapPrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(WrapPrescription.should_include(builder_context)) == [
            {
                "package_name": "flask",
                "match": {
                    "state": {
                        "resolved_dependencies": [
                            {
                                "name": "flask",
                                "version": "<=1.0.0,>=0.12",
                                "index_url": "https://pypi.org/simple",
                            }
                        ],
                    },
                },
                "run": {
                    "justification": [
                        {
                            "type": "ERROR",
                            "message": "This message will not be shown",
                            "link": "https://pypi.org/project/connexion",
                        }
                    ]
                },
            }
        ]

    def test_should_include_multi(self) -> None:
        """Test including this pipeline unit multiple times."""
        prescription_str = """
name: WrapUnit
type: wrap
should_include:
  times: 1
  adviser_pipeline: true
match:
  - state:
      resolved_dependencies:
        - name: tensorflow-cpu
  - state:
      resolved_dependencies:
        - name: tensorflow
  - state:
      resolved_dependencies:
        - name: intel-tensorflow
run:
  justification:
    - type: ERROR
      message: This message will be shown
      link: https://pypi.org/project/tensorflow
"""
        flexmock(WrapPrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_WRAP_SCHEMA(prescription)
        WrapPrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(WrapPrescription.should_include(builder_context)) == [
            {
                "package_name": "tensorflow-cpu",
                "match": {
                    "state": {
                        "resolved_dependencies": [
                            {
                                "name": "tensorflow-cpu",
                            }
                        ],
                    },
                },
                "run": {
                    "justification": [
                        {
                            "type": "ERROR",
                            "message": "This message will be shown",
                            "link": "https://pypi.org/project/tensorflow",
                        }
                    ]
                },
            },
            {
                "package_name": "tensorflow",
                "match": {
                    "state": {
                        "resolved_dependencies": [
                            {
                                "name": "tensorflow",
                            }
                        ],
                    },
                },
                "run": {
                    "justification": [
                        {
                            "type": "ERROR",
                            "message": "This message will be shown",
                            "link": "https://pypi.org/project/tensorflow",
                        }
                    ]
                },
            },
            {
                "package_name": "intel-tensorflow",
                "match": {
                    "state": {
                        "resolved_dependencies": [
                            {
                                "name": "intel-tensorflow",
                            }
                        ],
                    },
                },
                "run": {
                    "justification": [
                        {
                            "type": "ERROR",
                            "message": "This message will be shown",
                            "link": "https://pypi.org/project/tensorflow",
                        }
                    ]
                },
            },
        ]

    def test_should_include_no_package_name(self) -> None:
        """Test including this pipeline unit without any specific resolved package."""
        prescription_str = """
name: WrapUnit
type: wrap
should_include:
  times: 1
  adviser_pipeline: true
run:
  justification:
    - type: ERROR
      message: This message will not be shown
      link: https://pypi.org/project/connexion
"""
        flexmock(WrapPrescription).should_receive("_should_include_base").replace_with(lambda _: True).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_WRAP_SCHEMA(prescription)
        WrapPrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(WrapPrescription.should_include(builder_context)) == [
            {
                "package_name": None,
                "match": {},
                "run": {
                    "justification": [
                        {
                            "type": "ERROR",
                            "message": "This message will not be shown",
                            "link": "https://pypi.org/project/connexion",
                        }
                    ]
                },
            },
        ]

    def test_no_should_include(self) -> None:
        """Test not including this pipeline unit."""
        prescription_str = """
name: WrapUnit
type: wrap
should_include:
  times: 1
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      - name: flask
        version: "<=1.0.0,>=0.12"
        index_url: "https://pypi.org/simple"
run:
  justification:
    - type: ERROR
      message: This message will not be shown
      link: https://pypi.org/project/connexion
"""
        flexmock(WrapPrescription).should_receive("_should_include_base").replace_with(lambda _: False).once()
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_WRAP_SCHEMA(prescription)
        WrapPrescription.set_prescription(prescription)

        builder_context = flexmock()
        assert list(WrapPrescription.should_include(builder_context)) == []

    def test_advised_manifest_changes(self, state: State, context: Context) -> None:
        """Test advising changes in the manifest files."""
        prescription_str = """
name: WrapUnit
type: wrap
should_include:
  times: 1
  adviser_pipeline: true
match:
  state:
    resolved_dependencies:
      - name: intel-tensorflow
run:
  advised_manifest_changes:
    apiVersion: apps.openshift.io/v1
    kind: DeploymentConfig
    patch:
      op: add
      path: /spec/template/spec/containers/0/env/0
      value:
        name: OMP_NUM_THREADS
        value: "1"
"""
        prescription = yaml.safe_load(prescription_str)
        PRESCRIPTION_WRAP_SCHEMA(prescription)
        WrapPrescription.set_prescription(prescription)
        state.add_resolved_dependency(("intel-tensorflow", "2.2.0", "https://pypi.org/simple"))

        state.justification.clear()
        assert state.advised_manifest_changes == []

        unit = WrapPrescription()
        unit.pre_run()
        with unit.assigned_context(context):
            assert unit.run(state) is None

        assert state.advised_manifest_changes == [
            {
                "apiVersion": "apps.openshift.io/v1",
                "kind": "DeploymentConfig",
                "patch": {
                    "op": "add",
                    "path": "/spec/template/spec/containers/0/env/0",
                    "value": {"name": "OMP_NUM_THREADS", "value": "1"},
                },
            }
        ]
