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

"""A liveness probe run in OpenShift.

This liveness probe is run by OpenShift in a deployment where adviser computes
results. It's intention is to:

1. Notify about soon-to-terminate pod by using SIGUSR1 - adviser's predictor
should wrap up work and perform exploitation phase.

2. Send SIGINT to notify resolver to stop the resolution and report results
computed so far.

This Python script *HAS TO* be run in a container as it kills all the processes
except the main process (PID 1).
"""

import sys
import os
import signal
from pathlib import Path

# Create this file on kill for better reports in adviser logs.
_LIVENESS_PROBE_KILL_FILE = "/tmp/thoth_adviser_cpu_timeout"


def main() -> int:
    """Kill all processes except for main."""
    pids = [int(pid) for pid in os.listdir("/proc") if pid.isdigit()]

    liveness_file = Path(_LIVENESS_PROBE_KILL_FILE)
    if liveness_file.exists():
        signal_num = signal.SIGINT
    else:
        liveness_file.touch()
        signal_num = signal.SIGUSR1

    for pid in pids:
        if pid == 1:
            # No attempt to kill main process.
            continue
        if os.getpid() == pid:
            # Do not commit suicide.
            continue

        print("Killing process with PID %d with %d" % (pid, signal_num))
        os.kill(pid, signal_num)

    # Let liveness probe always fail with timeout.
    signal.pause()
    return 1


if __name__ == "__main__":
    sys.exit(main())
