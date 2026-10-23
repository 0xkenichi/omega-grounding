"""grounding_core.metta and evidence.combine must agree.

Needs a PeTTa checkout and an Omega checkout:
    PETTA_PATH=/path/to/PeTTa OMEGA_PATH=/path/to/PeTTa/repos/Omega pytest tests/test_metta_parity.py
PETTA_RUN overrides the launcher (default: PeTTa's run.sh).
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

from omega_grounding.evidence import Evidence, Verdict, combine
from omega_grounding.nal import Truth, fmt, parse

PETTA = os.environ.get("PETTA_PATH")
OMEGA = os.environ.get("OMEGA_PATH")
CORE = Path(__file__).resolve().parents[1] / "plugin" / "grounding" / "grounding_core.metta"

pytestmark = pytest.mark.skipif(not (PETTA and OMEGA), reason="set PETTA_PATH and OMEGA_PATH")

DM = parse("(--> dolphin mammal)")
MD = parse("(--> mammal dolphin)")
CASES = [
    (DM, Truth(1.0, 0.9), Evidence(Verdict.SUPPORTS, Truth(1.0, 0.7), "s", "p")),
    (MD, Truth(1.0, 0.9), Evidence(Verdict.REFUTES, Truth(0.0, 0.7), "s", "p", correction=DM)),
    (MD, Truth(0.0, 0.8), Evidence(Verdict.REFUTES, Truth(0.0, 0.7), "s", "p", correction=DM)),
    (DM, Truth(1.0, 0.9), Evidence.unknown("none")),
    (DM, Truth(1.0, 0.85), Evidence(Verdict.REFUTES, Truth(0.0, 0.7), "s", "p")),
]


def test_metta_matches_python(tmp_path):
    lines = [f"!(import! &self {Path(OMEGA) / 'lib_nal'})", f"!(import! &self {CORE.with_suffix('')})"]
    for statement, truth, evidence in CASES:
        lines.append(f"!(grounding-combine ({fmt(statement)} {truth}) {evidence.to_metta()} 0.15)")
    program = tmp_path / "parity.metta"
    program.write_text("\n".join(lines) + "\n")
    runner = os.environ.get("PETTA_RUN", str(Path(PETTA) / "run.sh"))
    out = subprocess.run(["sh", runner, str(program)], cwd=PETTA,
                         capture_output=True, text=True, timeout=300).stdout
    out = re.sub(r"\x1b\[[0-9;]*m", "", out)  # PeTTa colours its output

    # (grounded VERDICT (STATEMENT (stv F C)) TIER "provenance")
    results = [parse(line) for line in out.splitlines() if line.startswith("(grounded ")]
    assert len(results) == len(CASES), out
    for (statement, truth, evidence), (_, verdict, (stmt, stv), tier, _) in zip(CASES, results):
        expected = combine(statement, truth, evidence, 0.15)
        assert verdict == expected.verdict.value
        assert stmt == expected.statement
        assert float(stv[1]) == pytest.approx(expected.truth.f, abs=1e-4)
        assert float(stv[2]) == pytest.approx(expected.truth.c, abs=1e-4)
        assert tier == expected.tier
