#!/bin/sh
# PETTA_RUN launcher for the MeTTa tests: hosts PeTTa from Python (janus_swi) so py-call
# uses this Python environment. Needs PETTA_PATH; PYTHON defaults to python3.
exec "${PYTHON:-python3}" "$(dirname "$0")/run_metta.py" "$@"
