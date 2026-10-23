"""Run MeTTa files with PeTTa hosted in Python (janus_swi), so py-call uses this venv's Python.

The SWI-Prolog app's own janus is built for a system-wide python.org Python 3.11;
hosting Prolog from Python avoids needing that admin install.
"""
import os
import sys

PETTA = os.environ.get("PETTA_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "PeTTa"))
sys.path.insert(0, os.path.join(PETTA, "python"))
from petta import PeTTa  # noqa: E402

runner = PeTTa(petta_path=PETTA)
for path in sys.argv[1:]:
    for result in runner.load_metta_file(path):
        print(result)
