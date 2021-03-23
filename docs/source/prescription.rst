.. _prescription:

Declarative prescription for resolver
-------------------------------------

The implementation allows to declaratively specify pipeline units that should
be included in the resolver pipeline without actually implementing any Python
classes. The document below describes core mechanics behind creating such
prescription for the resolver. Note the declarative prescription allows to
quickly provide pipeline units that assist the resolution process but have
limited expressive capabilities. For more sophisticated pipeline units one can
still use the programmable interface.

One can see prescriptions as `enhanced constraints
<https://pip.pypa.io/en/stable/user_guide/#constraints-files>`_ but on the
server side. This way constraints can be generalized and applied also for
multiple projects for which server-side resolution can provide guidance.

.. note::

  Prescription YAML specification provides unit abstractions that map to their
  Python code implementation. If you wish to create your own unit declaration
  in the YAML configuration suitable for your needs, just declare your YAML
  unit and provide its Python implementation. Core pipeline units can serve as
  a base for the implementation.

Prescription YAML v1
====================

.. note::

  Check `thoth-station/adviser repository
  <https://github.com/thoth-station/adviser/blob/master/thoth/adviser/prescription/v1/schema.py>`__
  to see the precise definition of the schema.

Each prescription YAML v1 document states the following core parts that will be
discussed in detail in the upcoming sections.

.. code-block:: yaml

  apiVersion: thoth-station.ninja/v1
  kind: prescription
  spec:
    name: thoth
    release: 2021.03.30
    units:
      boots: []
      pseudonyms: []
      sieves: []
      steps: []
      strides: []
      wraps: []

The semantics behind entries stated:

``apiVersion``
##############

API version of the prescription.

Prescription units are versioned and provide certain capabilities to describe
the resolution process. Prescriptions implementing different API version can
provide different semantics or different feature set. Make sure you refer to
the right API version when using prescriptions.

``kind``
########

Always set to ``prescription``.

``spec``
########

Prescription specification.

``spec.name``
#############

Name of the prescription used to create namespace for declared prescription
units.

*Example:* ``thoth``

``spec.release``
################

A release identifier for the prescription.

*Example:* A `calver <https://calver.org/>`__ can be used - ``2020.03.30``

``spec.units``
##############

Units specified by the prescription grouped into categories based on their
types.

Unit schema
===========

Each unit, regardless of its type, has the following schema:

.. code-block:: yaml

  name: '<unit_name>'
  type: '<unit_type>'
  should_include:
    <should_include_section>
  run:
    <run_section>

The semantics behind entries:

``name``
########

Name of the unit that uniquely identifies the unit of the specific type.

All the units created based on prescription live in their own namespace that is
specified by the ``name`` of the prescription. This makes sure unit names do
not clash across multiple prescriptions supplied.

``type``
########

Type of the unit, one of ``boot``, ``pseudonym``, ``sieve``, ``step``,
``stride`` and ``wrap``.

Including a unit - ``should_include``
=====================================

``should_include.times``
########################

Number of times the given unit should be included in the resolution process.

Possible values:

* ``1`` - the given pipeline unit should be included once in the resolution
  process if all the criteria for including it match (default)

* ``0`` - the given pipeline unit will not be included in the resolution
  process - the given pipeline unit is off even thought it is stated in the
  YAML file

``should_include.adviser_pipeline``
###################################

Boolean stating whether the given pipeline pipeline unit will be part of
"adviser" pipeline used for computing Thoth's recommendations.

Possible values:

* ``false`` - the given pipeline unit will not be part of the resolver pipeline
  when computing advises (default)

* ``true`` - the given pipeline unit will be part of the resolver pipeline
  when computing advises

``should_include.recommendation_types``
#######################################

A list of recommendation types that should be matched if the unit is registered
for the adviser resolution pipeline.

If ``adviser_pipeline`` is set to ``false``, this configuration option has no
effect.

See `the listing of recommendation types available
<https://thoth-station.ninja/recommendation-types/>`__.

``should_include.dependency_monkey_pipeline``
#############################################

Boolean stating whether the given pipeline pipeline unit will base part of
:ref:`Dependency Monkey <dependency_monkey>` pipeline used for `data
acquisition and generation on Amun
<https://github.com/thoth-station/amun-api/>`__.

Possible values:

* ``false`` - the given pipeline unit will not be part of the resolver pipeline
  used for Dependency Monkey (default)

* ``true`` - the given pipeline unit will be part of the resolver pipeline
  when running Dependency Monkey

``should_include.decision_types``
#################################

A list of decision types that should be matched if the unit is registered for
the :ref:`Dependency Monkey <dependency_monkey>` resolution pipeline used for
`data acquisition on Amun <https://github.com/thoth-station/amun-api/>`__.

If ``dependency_monkey_pipeline`` is set to ``false``, this configuration
option has no effect.

``should_include.library_usage``
================================

Library calls that should be present to include the pipeline unit. This
creates an ability to include a pipeline unit only if some parts of a
library are used that affect the application.

.. note::

  *Example:*

  .. code-block:: yaml

    library_usage:
      # from flask import Flask
      flask:
        Flask

``should_include.dependencies``
###############################

Dependencies on other pipeline units. All the stated pipeline units have to be
registered (``should_include`` has to be evaluated as ``true``) as listed
dependencies are pre-requisites to register the stated pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    should_include:
      dependencies:
        boots:
          - thoth.ExampleBoot
          - CoreBoot

  This part of the ``should_include`` section is specific to a unit that states
  dependencies on two units of type :ref:`boot <boots>`. ``ExampleBoot`` is a boot
  pipeline unit from prescription named ``thoth`` and ``CoreBoot`` is a boot
  provided by the adviser Python implementation (corresponds to a name of the
  Python class).

Referencing unknown units evaluates always to ``false``.

If no dependencies are stated, the given pipeline unit is not dependent on
any pipeline unit.

``should_include.dependencies.boots``
#####################################

A list of :ref:`boot pipeline units <boots>` that need to be present in the
resolution process. Referenced by respective unit name and optional
prescription name for referencing units from prescriptions (see above for more
info).

``should_include.dependencies.pseudonyms``
##########################################

A list of :ref:`pseudonym pipeline units <pseudonyms>` that need to be present
in the resolution process.  Referenced by respective unit name and optional
prescription name for referencing units from prescriptions (see above for more
info).

``should_include.dependencies.sieves``
######################################

A list of :ref:`sieve pipeline units <sieves>` that need to be present in the
resolution process.  Referenced by respective unit name and optional
prescription name for referencing units from prescriptions (see above for more
info).

``should_include.dependencies.steps``
#####################################

A list of :ref:`step pipeline units <steps>` that need to be present in the
resolution process.  Referenced by respective unit name and optional
prescription name for referencing units from prescriptions (see above for more
info).

``should_include.dependencies.strides``
#######################################

A list of :ref:`stride pipeline units <strides>` that need to be present in the
resolution process.  Referenced by respective unit name and optional
prescription name for referencing units from prescriptions (see above for more
info).

``should_include.dependencies.wraps``
#####################################

A list of :ref:`wrap pipeline units <wraps>` that need to be present in the
resolution process.  Referenced by respective unit name and optional
prescription name for referencing units from prescriptions (see above for more
info).

Runtime environments - ``should_include.runtime_environments``
==============================================================

Matching runtime environment configurations for which pipeline units should be
included in the resolution process. This configuration section is meant for
units that are specific for runtime environments.

``should_include.runtime_environments.operating_systems``
#########################################################

A list of operating systems for which the pipeline unit should be included.
Each entry optionally states ``name`` (operating system name) and ``version``
(operating system version). Not providing any of the two means matching *any*
value.

.. note::

  *Example:*

  .. code-block:: yaml

    operating_systems:
      - name: rhel     # matches Red Hat Enterprise Linux in any version
      - name: fedora   # matches Fedora in version 33
        version: 33

``should_include.runtime_environments.hardware``
################################################

Matching hardware available when running the application. This
configuration basically creates a matrix of hardware that should be
available on user's side to register the given pipeline unit in the
resolution process.

.. note::

  *Example:*

  .. code-block:: yaml

    hardware:
      # Matches any GPU or no GPU available and
      # CPU family 1 CPU model 9 or CPU family 2 and CPU model 8.
      - cpu_families: [1, 2]
        cpu_models: [9, 8]

      # Matches CPU family 1, CPU model 9 running on GPU "Foo" or GPU "Bar",
      - cpu_families: [1]
        cpu_models: [9]
        gpu_models:
          - Foo
          - Bar

``should_include.runtime_environments.python_versions``
#######################################################

A list of Python versions that need to be matched for including the
given pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    python_versions:
      # Match when running 3.8 or 3.9:
      - '3.8'
      - '3.9'

If this configuration option is not provided, it defaults to any
Python version.

Python version is always in form of ``<major>.<minor>``. Patch versions
are not considered.

``should_include.runtime_environments.cuda_versions``
#####################################################

A list of Nvidia CUDA versions that need to be matched for including the given
pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    cuda_versions:
      # Match when running CUDA 9.0 or 9.2.
      - '9.0'
      - '9.2'

  If this configuration option is not provided, it defaults to any
  CUDA version - even if none available.

A special value of ``null`` means no CUDA version available.

.. note::

  *Example:*

  .. code-block:: yaml

    cuda_versions:
      # Match when running CUDA 9.1 or no CUDA available.
      - '9.1'
      - null

``should_include.runtime_environments.platforms``
#################################################

A list of platforms for which the given pipeline unit should be registered.

.. note::

  *Example:*

  .. code-block:: yaml

    platforms:
      - linux-x86_64

If this configuration option is not supplied, it defaults to *any* platform.

``should_include.runtime_environments.openblas_versions``
#########################################################

A list of `OpenBLAS <https://www.openblas.net/>`__ versions that need to be
matched for including the given pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    openblas_versions:
      # Match when running OpenBLAS 0.3.13, 0.3.0.
      - '0.3.13'
      - '0.3.0'

  If this configuration option is not provided, it defaults to any OpenBLAS
  version - even none available.

A special value of ``null`` means no OpenBLAS version available.

.. note::

  *Example:*

  .. code-block:: yaml

    openblas_versions:
      # Match when running OpenBLAS 0.3.13 or no OpenBLAS is available.
      - '0.3.13'
      - null

``should_include.runtime_environments.openmpi_versions``
########################################################

A list of `OpenMPI <https://www.open-mpi.org/>`__ versions that need to be
matched for including the given pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    openmpi_versions:
      # Match when running OpenMPI 4.1.0 or 4.0.5
      - '4.1.0'
      - '4.0.5'

  If this configuration option is not provided, it defaults to any OpenMPI
  version - even none available.

A special value of ``null`` means no OpenMPI version available.

.. note::

  *Example:*

  .. code-block:: yaml

    openblas_versions:
      # Match when no OpenMPI is available.
      - null

``should_include.runtime_environments.cudnn_versions``
######################################################

A list of Nvidia cuDNN versions that need to be matched for including the given
pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    cudnn_versions:
      # Match when running cuDNN 8.0.5 or 7.6.5
      - '8.0.5'
      - '7.6.5'

  If this configuration option is not provided, it defaults to any cuDNN version
  - even none available.

A special value of ``null`` means no cuDNN version available.

.. note::

  *Example:*

  .. code-block:: yaml

    cudnn_versions:
      # Match when no cuDNN is available.
      - null

``should_include.runtime_environments.mkl_versions``
####################################################

A list of `Intel MKL
<https://software.intel.com/content/www/us/en/develop/articles/oneapi-math-kernel-library-release-notes.html>`__
versions that need to be matched for including the given pipeline unit.

.. note::

  *Example:*

  .. code-block:: yaml

    mkl_versions:
      # Match when running MKL 2021.1
      - '2021.1'

  If this configuration option is not provided, it defaults to any MKL
  version - even none available.

A special value of ``null`` means no MKL version available.

.. note::

  *Example:*

  .. code-block:: yaml

    mkl_versions:
      # Match when no Intel MKL is available.
      - null

``should_include.runtime_environments.base_images``
###################################################

A list of base images that are used as a runtime environment when running the
application. These base images map to `Thoth's S2I container images
<https://github.com/thoth-station/s2i-thoth>`__ or container images produced by
the `AICoE-CI pipeline <https://github.com/AICoE/aicoe-ci>`__.

.. note::

  *Example:*

  .. code-block:: yaml

    base_images:
      # Match UBI8 Python 3.8 container environment or UBI8 Python 3.6 container
      # environment in specific versions.
      - quay.io/thoth-station/s2i-thoth-ubi8-py38:v1.0.0
      - quay.io/thoth-station/s2i-thoth-ubi8-py36:v0.8.1

Boots
=====

Declaring :ref:`pipeline units of type boot <boots>`.

The following example shows all the configuration options that can be applied
for a boot pipeline unit type. See respective sections described below for more
info. Also note, the example shows all the options that can be supplied and is
not semantically valid (not all options can be supplied at the same time
semantically):

.. code-block:: yaml

  name: BootUnit
  type: boot
  should_include:
    # See should_include section for more info.
  run:
    match:                                          # Criteria to trigger run of this pipeline unit. Defaults to always running the boot pipeline unit if no package_name is provided.
      package_name: flask                           # Name of the package that needs to be present in the direct dependency listing to run this unit.

    stack_info:                                     # Information printed to the recommended stack report.
      - type: ERROR
        message: "Unable to perform this operation"
        link: https://thoth-station.ninja           # A link to stack info or a link to a web page.

    # Configuration of prematurely terminating the resolution process - the
    # message will be reported to the user. If this configuration option is not
    # set, the resolver will not terminate when running this unit.
    eager_stop_pipeline: "Terminating resolution as 'flask' is in direct dependencies."

     # Configuration of prematurely terminating the resolution process.
    not_acceptable: "Cannot include this package"

    log:
      message: "Some text printed to log on pipeline unit run."
      type: "WARNING"

Boot ``run.match.package_name``
###############################

Optional name of the package that should be present in direct dependencies to
trigger run of the pipeline unit.

*Example:*

.. code-block:: yaml

  name: BootUnit
  type: boot
  should_include:
    adviser_pipeline: true
  run:
    match:
      package_name: flask
    log:
      type: WARNING
      message: Found package 'flask' in the direct dependency listing

.. _boot_stack_info:

Boot ``run.stack_info``
#######################

Optional a list of information added to the "stack info" field that is
:ref:`specific for the application stack <stack_info>`.

Each entry in the list is specified by three attributes:

* ``type`` - any of ``INFO``, ``WARNING``, and ``ERROR`` specifying severity of the produced info
* ``message`` - a message in free text form printed to users
* ``link`` - a link to a document describing more information in detail

The link can be in a form of a valid HTTP or HTTPS URL or a string which
:ref:`references justifications <jl>` available at
`thoth-station.ninja/justifications
<https://thoth-station.ninja/justifications>`__.

.. note::

  *Example:*

  .. code-block:: yaml

    name: BootUnit
    type: boot
    should_include:
      adviser_pipeline: true
      recommendation_types:
        - performance
      runtime_environments:
        operating_systems:
          - name: rhel
            version: '8'
        python_versions: ['3.6']
    run:
      stack_info:
        - type: WARNING
          message: It is recommended to switch to Python 3.8 to improve performance
          link: 'https://developers.redhat.com/blog/2020/06/25/red-hat-enterprise-linux-8-2-brings-faster-python-3-8-run-speeds/'

Boot ``run.eager_stop_pipeline``
################################

An optional string describing exception that should be raised during resolver
boot causing the resolution process to halt.

.. note::

  *Example:*

  .. code-block:: yaml

    name: BootUnit
    type: boot
    should_include:
      adviser_pipeline: true
      recommendation_types:
        - security
      runtime_environments:
        operating_systems:
          - name: fedora
    run:
      eager_stop_pipeline: Security recommendation types are disabled for Fedora, use RHEL instead

.. _boot_run_log:

Boot ``run.log``
################

Print the given message to logs if the pipeline unit is included and run.

.. note::

  *Example:*

  .. code-block:: yaml

    name: BootUnit
    type: boot
    should_include:
      adviser_pipeline: true
      dependency_monkey_pipeline: true
    run:
      log:
        message: Using prescriptions in the resolution process
        type: INFO

Pseudonyms
==========

Declaring :ref:`pipeline units of type pseudonym <pseudonyms>`.

The following example shows all the configuration options that can be applied
for a pseudonym pipeline unit type. See respective sections described below for more
info. Also note, the example shows all the options that can be supplied and is
not semantically valid (not all options can be supplied at the same time
semantically):

.. code-block:: yaml

  name: PseudonymUnit
  type: pseudonym
  should_include:                                   # See should_include section.
  run:
    match:                                          # Criteria to trigger run of this pipeline unit. Defaults to always running the pseudonym pipeline unit if no package_version is provided.
      package_version:
        name: flask                                 # Mandatory, name of the package for which pseudonym should be registered.
        version: '>1.0,<=1.1.0'                     # Version specifier for which the pseudonym should be run. If not provided, defaults to any version.
        index_url: 'https://pypi.org/simple'        # Package source index for which the pseudonym should be run. If not provided, defaults to any index.

    log:                                            # Optional text printed to logs when the unit gets called.
      message: "Some text printed to log on pipeline unit run."
      type: "WARNING"

    stack_info:                                     # Information printed to the recommended stack report.
      - type: WARNING
        message: "Hello, world"
        link: https://thoth-station.ninja           # A link to justifications or a link to a web page.

    yield:
      # Pseudonym that should be registered.
      yield_matched_version: true                   # If set to true, use version that was matched instead of the one provided in the locked_version part.
      package_version:
        name: flask                                 # Mandatory, name of the pseudonym package.
        locked_version: '==1.2.0'                          # Version of the pseudonym in a locked form.
        index_url: 'https://pypi.org/simple'        # Package source index where the pseudonym is hosted.

The pseudonym is registered for the specified criteria. The unit derived out of
this declarative prescription will make sure the package yielded is known to
the resolver.

Pseudonym ``run.log``
#####################

Print the given message to logs if the pipeline unit is included and run.

See :ref:`boot's log <boot_run_log>` that has shared semantics.

Pseudonym ``run.stack_info``
############################

See :ref:`stack info <boot_stack_info>` which semantics is shared with this unit.

Note stack info is added only once even if the pipeline unit is
run multiple times during the resolution process.

Pseudonym ``run.match``
#######################

Package described in ``package_version`` field that should be matched by three
entries:

* ``name`` - mandatory, name of the package for which the pseudonym should be
  provided
* ``version`` - optional, version in a form of version specifier for which the
  pseudonym should be provided
* ``index_url`` - optional, Python package index URL for which the pseudonym
  should be provided

See examples below for more info.

Pseudonym ``run.yield``
#######################

Description of a package that should be yielded. Made out of two entries:

* ``yield_matched_version`` - yields version that was matched based on version
  specifier in the ``match`` section, defaults to ``false``
* ``package_version`` - description of a package that should be yielded

  * ``name`` - mandatory, name of the package that should be yielded
  * ``locked_version`` - optional, disjoint with ``yield_matched_version``;
    describes locked version of the package that should be yielded
  * ``index_url`` - optional, Python package index to be used to provide
    pseudonyms

If no version provided or no index explicitly set, all found in the database
(analyzed by Thoth) are yielded.

.. note::

  An example pipeline unit that suggests ``intel-tensorflow`` coming from PyPI
  as an alternative to ``tensorflow``:

  .. code-block:: yaml

    name: PseudonymUnit
    type: pseudonym
    should_include:
      times: 1
      adviser_pipeline: true
    run:
      match:
        package_version:
          name: tensorflow
          index_url: "https://pypi.org/simple"

      stack_info:
        - message: "Considering also intel-tensorflow as an alternative to tensorflow"
          type: "INFO"
          link: "https://pypi.org/project/intel-tensorflow"

      yield:
        yield_matched_version: true
        package_version:
          name: intel-tensorflow
          index_url: "https://pypi.org/simple"

Sieves
======

Declaring :ref:`pipeline units of type sieve <sieves>`.

The following example shows all the configuration options that can be applied
for a sieve pipeline unit type. See respective sections described below for more
info. Also note, the example shows all the options that can be supplied and is
not semantically valid (not all options can be supplied at the same time
semantically):

.. code-block:: yaml

  name: SieveUnit
  type: sieve
  should_include:                                   # See should_include section.
  run:
    match:                                          # Criteria to trigger run of this pipeline unit. Defaults to always running the sieve pipeline unit if no package_version is provided.
      package_version:                              # Any package matching this criteria will be filtered out from the resolution.
        name: flask                                 # Name of the package for which the unit should be registered.
        version: '>1.0,<=1.1.0'                      # Version specifier for which the sieve should be run. If not provided, defauts to any version.
        index_url: 'https://pypi.org/simple'        # Package source index for which the sieve should be run. If not provided, defaults to any index.

    log:                                            # Optional text printed to logs when the unit gets called.
      message: "Some text printed to log on pipeline unit run."
      type: "WARNING"

    stack_info:                                     # Information printed to the recommended stack report.
      - type: WARNING
        message: "Hello, world"
        link: https://thoth-station.ninja           # A link to justifications or a link to a web page.

Sieve ``run.match``
###################

Specifies a package version that should be matched to execute the given unit during
in the resolution pipeline.

The package is described by:

* ``name`` - name of the Python package that should be matched, any package
  name matched if not provided
* ``version`` - version in a form of version specification to be matched, any
  version matched if not provided
* ``index_url`` - URL of the Python package index from where the given package
  is consumed, matches any index if not provided

.. note::

  *Example:*

  .. code-block:: yaml

    name: SieveUnit
    type: sieve
    should_include:
      adviser_pipeline: true
      recommendation_types:
        - security
    run:
      match:
        package_version:
          index_url: 'https://pypi.org/simple'

      stack_info:
        - type: WARNING
          message: "Filtering out all the packages from PyPI for security reasons"
          link: "https://pypi.org/simple"

Sieve ``run.log``
#################

Print the given message to logs if the pipeline unit is included and run.


.. note::

  *Example:*

  .. code-block:: yaml

    name: SieveUnit
    type: sieve
    should_include:
      times: 1
      adviser_pipeline: true
      runtime_environments:
        python_versions: ['3.5', '3.6', '3.7', '3.8', '3.9']
    run:
      match:
        package_version:
          name: enum34
      log:
        type: WARNING
        message: All releases of package 'enum34' were filtered out

      stack_info:
        - type: WARNING
          message: All releases of package 'enum34' were filtered out
          link: 'http://pypi.org/project/enum34'

See :ref:`boot's log <boot_run_log>` that has shared semantics.

Sieve ``run.stack_info``
########################

See :ref:`stack info <boot_stack_info>` which semantics is shared with this unit.

Note stack info is added only once even if the pipeline unit is
run multiple times during the resolution process.

.. note::

  An example pipeline unit that filters out ``pysaml2`` with the reported CVE.

  .. code-block:: yaml

    name: SieveUnit
    type: sieve
    should_include:
      times: 1
      adviser_pipeline: true
      recommendation_types:
        - security
        - stable
    run:
      match:
        package_version:
          name: pysaml2
          version: '<6.5.0'
          index_url: 'https://pypi.org/simple'

      stack_info:
        - type: WARNING
          message: "Not considering package pysaml2 based on vulnerability present"
          link: "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-21238"

Steps
=====

Declaring :ref:`pipeline units of type step <steps>`.

The following example shows all the configuration options that can be applied
for a step pipeline unit type. See respective sections described below for more
info. Also note, the example shows all the options that can be supplied and is
not semantically valid (not all options can be supplied at the same time
semantically):

.. code-block:: yaml

  name: StepUnit
  type: step
  should_include:                                   # See should_include section.
  run:
    match:                                          # Criteria to trigger run of this pipeline unit. Defaults to always running the boot pipeline unit if no package_version is provided.
      package_version:                              # Any package matching this criteria will be filtered out from the resolution.
        name: flask                                 # Name of the package for which the unit should be registered.
        version: '>1.0,<=1.1.0'                      # Version specifier for which the sieve should be run. If not provided, defaults to any version.
        index_url: 'https://pypi.org/simple'        # Package source index for which the sieve should be run. If not provided, defaults to any index.

      state:                                        # Optional, resolver internal state to match for the given resolution step.
        resolved_dependencies:
          - name: werkzeug                          # Dependencies that have to be present in the resolved state.
            version: "==1.0.0"
            index_url: 'https://pypi.org/simple'

    score: 0.42                                     # Score assigned to the step performed in the resolution.
    justification:
      - type: INFO
        message: "Hello, Thoth!"
        link: https://thoth-station.ninja

    not_acceptable: "Bad package inclusion"         # Block including certain package during the resolution.

    # Configuration of prematurely terminating the resolution process.
    eager_stop_pipeline: "Stop pipeline"

    multi_package_resolution: false                 # Run this pipeline multiple times when matched mutliple times. Defaults to false if not provided.

    log:                                            # Optional text printed to logs when the unit gets called.
      message: "Some text printed to log on pipeline unit run."
      type: "WARNING"

    stack_info:                                     # Information printed to the recommended stack report.
      - type: WARNING
        message: "Hello, world"
        link: https://thoth-station.ninja           # A link to justifications or a link to a web page.

Step ``run.match``
##################

Match the given step performed in the resolution process. A step is described
by state stating all the resolved dependencies so far and package that is
about to be resolved:

* ``package_version`` - package that is about to be resolved by adding it to
  the resolver's state

  * ``name`` - optional, name of the package
  * ``version`` - optional, version in a form of version specifier
  * ``index_url`` - optional, Python package index URL

* ``state`` - internal resolver's state with resolved dependencies

A state that needs to be met to trigger the given step pipeline. The state
states resolved dependencies where each entry in the resolved dependency
listing is described as:

* ``name`` - optional package name that has to be stated in the resolved
  dependency listing
* ``version`` - optional package version in a form of version specifier that
  has to be stated in the resolved dependency listing
* ``index_url`` - optional package index from which the given package is
  consumed

To run the given step, all the packages in the resolved dependency listing
need to be present in the resolved software stack.

To run the given step, both ``state`` and ``package_version`` need to be
matched.

Step ``run.log``
################

Print the given message to logs if the pipeline unit is included and run.

See :ref:`boot's log <boot_run_log>` that has shared semantics.

Step ``run.stack_info``
#######################

See :ref:`stack info <boot_stack_info>` which semantics is shared with this unit.

Note stack info is added only once even if the pipeline unit is
run multiple times during the resolution process.

Step ``run.multi_package_resolution``
#####################################

Boolean stating whether the given unit should be run if criteria match multiple
times per resolution run. Defaults to false.

.. _step_run_justification:

Step ``run.justification``
##########################

Optional justification added to the resolved stack when the pipeline unit is
run. This justification is added only if no ``not_acceptable`` and no
``eager_stop_pipeline`` are supplied - if the given step is a valid step in the
resolution process. See :ref:`justification` for more info on how to write
justifications and their semantics.

Each entry in the list is specified by three attributes:

* ``type`` - any of ``INFO``, ``WARNING``, and ``ERROR`` specifying severity of
  the produced info
* ``message`` - a message in free text form printed to users
* ``link`` - a link to a document describing more information in detail

The link can be in a form of a valid HTTP or HTTPS URL or a string which
:ref:`references justifications <jl>` available at
`thoth-station.ninja/justifications
<https://thoth-station.ninja/justifications>`__.

.. note::

  *Example:*

  .. code-block:: yaml

    name: StepUnit
    type: step
    should_include:
      times: 1
      adviser_pipeline: true
    run:
      match:
        package_version:
          index_url: 'https://thoth-station.ninja/simple'

      score: +0.1

      justification:
        - type: INFO
          message: "Builds available on index thoth-station.ninja/simple take precedence"
          link: "https://thoth-station.ninja/"

Step ``run.score``
##################

Optional score addition to penalize or prioritize resolving the given stack.
Score has to be from interval -1.0 to +1.0 inclusively.

See :ref:`justification <step_run_justification>` for an example.

Step ``run.not_acceptable``
###########################

Make the given step not acceptable in the resolution process.

.. note::

  *Example:*

  A pipeline unit that filters out any ``tensorflow~=2.4.0`` when
  ``numpy==1.19.1`` is in already resolved dependencies.

  .. code-block:: yaml

    name: StepUnit
    type: step
    should_include:
      times: 1
      adviser_pipeline: true
    run:
      match:
        package_version:
          name: numpy
          version: "==1.19.1"
          index_url: 'https://pypi.org/simple'
        state:
          resolved_dependencies:
            # Considering builds available also on other indexes than PyPI.
            - name: tensorflow
              version: '~=2.4.0'

      multi_package_resolution: true

      not_acceptable: "NumPy==1.19.5 is causing issues when used with TensorFlow 2.4"

      stack_info:
        - type: WARNING
          message: "NumPy==1.19.5 is causing issues when used with TensorFlow 2.4"
          link: "https://thoth-station.ninja/j/tf_24_np.html"

Step ``run.eager_stop_pipeline``
################################

If the given pipeline unit is registered and matched, it will cause the whole
resolution to halt and report back any results computed.

Strides
=======

Declaring :ref:`pipeline units of type stride <strides>`.

The following example shows all the configuration options that can be applied
for a stride pipeline unit type. See respective sections described below for more
info. Also note, the example shows all the options that can be supplied and is
not semantically valid (not all options can be supplied at the same time
semantically):

.. code-block:: yaml

  name: StrideUnit
  type: stride
  should_include:                                   # See should_include section.
  run:
    match:                                          # Criteria to trigger run of this pipeline unit. Defaults to always running the boot pipeline unit if no package_version is provided.
      state:                                        # Optional, resolver internal state to match for the given stride.
        resolved_dependencies:
          - name: werkzeug                          # Dependencies that have to be present in the resolved state.
            version: "~=1.0.0"
            index_url: 'https://pypi.org/simple'

    log:                                            # Optional text printed to logs when the unit gets called.
      message: "Some text printed to log on pipeline unit run."
      type: "WARNING"

    stack_info:                                     # Information printed to the recommended stack report.
      - type: WARNING
        message: "Hello, world"
        link: https://thoth-station.ninja           # A link to justifications or a link to a web page.

    not_acceptable: "Bad package inclusion"         # Block resolving the given stack.

    # Configuration of prematurely terminating the resolution process.
    eager_stop_pipeline: "Stop pipeline"

Stride ``run.match``
####################

A state that needs to be met to trigger the given stride pipeline. The state
states resolved dependencies where each entry in the resolved dependency
listing is described as:

* ``name`` - optional package name that has to be stated in the resolved
  dependency listing
* ``version`` - optional package version in a form of version specifier that
  has to be stated in the resolved dependency listing
* ``index_url`` - optional package index from which the given package is
  consumed

To run the given stride, all the packages in the resolved dependency listing
need to be present in the resolved software stack.

Stride ``run.log``
##################

Print the given message to logs if the pipeline unit is included and run.

See :ref:`boot's log <boot_run_log>` that has shared semantics.

Stride ``run.stack_info``
#########################

See :ref:`stack info <boot_stack_info>` which semantics is shared with this unit.

Note stack info is added only once even if the pipeline unit is
run multiple times during the resolution process.

Stride ``run.not_acceptable``
#############################

If the given pipeline unit is registered and matched, it will discard the
resolved stack matched from the resolver's results reported.

Stride ``run.eager_stop_pipeline``
##################################

If the given pipeline unit is registered and matched, it will cause the whole
resolution to halt and report back any results computed.

Wraps
=====

Declaring :ref:`pipeline units of type wrap <wraps>`.

The following example shows all the configuration options that can be applied
for a wrap pipeline unit type. See respective sections described below for more
info. Also note, the example shows all the options that can be supplied and is
not semantically valid (not all options can be supplied at the same time
semantically):

.. code-block:: yaml

  name: WrapUnit
  type: wrap
  should_include:                                   # See should_include section.
  run:
    match:                                          # Criteria to trigger run of this pipeline unit. Defaults to always running the boot pipeline unit if no package_version is provided.
      state:                                        # Optional, resolver internal state to match for the given stride.
        resolved_dependencies:
          - name: werkzeug                          # Dependencies that have to be present in the resolved state.
            version: ">=1.0.0,<2.5.0"
            index_url: 'https://pypi.org/simple'

    not_acceptable: "Bad package inclusion"         # Block resolving the given stack.

    # Configuration of prematurely terminating the resolution process.
    eager_stop_pipeline: "Stop pipeline"

    log:                                            # Optional text printed to logs when the unit gets called.
      message: "Some text printed to log on pipeline unit run."
      type: "WARNING"

    stack_info:                                     # Information printed to the recommended stack report.
      - type: WARNING
        message: "Hello, world"
        link: https://thoth-station.ninja           # A link to justifications or a link to a web page.

    justification:
      - type: INFO
        message: "Hello, Thoth!"
        link: https://thoth-station.ninja

Wrap ``run.match``
##################

A state that needs to be met to trigger the given wrap pipeline unit. The state
states resolved dependencies where each entry in the resolved dependency
listing is described as:

* ``name`` - optional package name that has to be stated in the resolved
  dependency listing
* ``version`` - optional package version in a form of version specifier that
  has to be stated in the resolved dependency listing
* ``index_url`` - optional package index from which the given package is
  consumed

To run the given wrip unit, all the packages in the resolved dependency
listing need to be present in the resolved software stack.

Wrap ``run.log``
################

Print the given message to logs if the pipeline unit is included and run.

See :ref:`boot's log <boot_run_log>` that has shared semantics.

Wrap ``run.stack_info``
#######################

See :ref:`stack info <boot_stack_info>` which semantics is shared with this unit.

Note stack info is added only once even if the pipeline unit is
run multiple times during the resolution process.

.. note::

  *Example:*

  .. code-block:: yaml

    name: WrapUnit
    type: wrap
    should_include:
      adviser_pipeline: true
      recommendation_types:
        # Only warn here, in case of performance the corresponding resolution step can be penalized.
        - latest
        - testing
      library_usage:
        tensorflow:
          - tensorflow.keras.layers.Embedding
    run:
      match:
        state:
          resolved_dependencies:
            - name: tensorflow
              version: "<=2.4.0"

      stack_info:
        - type: WARNING
          message: "TensorFlow in version <=2.4 is slow when tf.keras.layers.Embedding is used"
          # Can be replaced with just "tf_42475".
          link: "https://thoth-station.ninja/j/tf_42475.html"

Wrap ``run.not_acceptable``
###########################

If the given pipeline unit is registered and matched, it will discard the
resolved stack matched from the resolver's results reported.

Wrap ``run.eager_stop_pipeline``
################################

If the given pipeline unit is registered and matched, it will cause the whole
resolution to halt and report back any results computed.

Wrap ``run.justification``
##########################

Justification added if the given wrap is matched and run. This justification is
similar to the one :ref:`as provided by step <step_run_justification>`. It is
added to the resolved stack if the match criteria are met. The unit cannot
provide ``eager_stop_pipeline`` or ``not_acceptable`` to have justification
available.
