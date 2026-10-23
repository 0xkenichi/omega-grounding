"""Load the plugin through Omega's own plugin loader and call the `ground` skill.

Runs a MeTTa program from the PeTTa directory the way Omega's run.metta does:
registers the Omega checkout as the `Omega` library, imports the Omega modules
the plugin uses, then loadPlugin + skill call. Sources are replayed from the
benchmark cassette, so no network is needed.

    PETTA_PATH=/path/to/PeTTa OMEGA_PATH=/path/to/PeTTa/repos/Omega pytest tests/test_omega_plugin.py
OMEGA_PATH/plugins/grounding must link to this repository's plugin/grounding
(plugin/install.sh does that). PETTA_RUN overrides the launcher (default: PeTTa's run.sh).
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

PETTA = os.environ.get("PETTA_PATH")
OMEGA = os.environ.get("OMEGA_PATH")
ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(not (PETTA and OMEGA), reason="set PETTA_PATH and OMEGA_PATH")

PROGRAM = """
!(import! &self (library lib_import))
!(git-import! "https://github.com/singnet/Omega.git" "" "{repos}")
!(import! &self (library Omega lib_nal))
!(import! &self (library Omega ./src/utils.py))
!(import! &self (library Omega ./src/utils))
!(import! &self (library Omega ./src/helper.py))
!(import! &self (library Omega ./src/config.py))
!(import! &self (library Omega ./src/config))
!(import! &self (library Omega ./src/logger.py))
!(import! &self (library Omega ./src/log))
!(import! &self (library Omega ./src/plugin.py))
!(import! &self (library Omega ./src/plugin))
!(import! &self (library Omega ./src/skills))

(= (command-line) ())
!(initConfig)
!(initLogger)

!(println! (loaded (loadMettaPlugin "grounding" "{plugins}/grounding")))
!(println! (skills (getSkills)))
!(println! (result (ground "((--> mammal dolphin) (stv 1.0 0.9))")))
!(println! (result (ground "((--> (× usdc 18) decimals) (stv 1.0 0.9))")))
!(println! (result (ground "((--> weth ([] upgradeable)) (stv 1.0 0.8))")))
!(import! &self (library lib_patrick))
!(println! (result (ground "((--> whale mammal) (stv 1.0 0.9))")))
"""


def test_plugin_loads_and_grounds(tmp_path):
    program = tmp_path / "omega_plugin.metta"
    program.write_text(PROGRAM.format(repos=Path(OMEGA).parent, plugins=Path(OMEGA) / "plugins"))
    env = dict(os.environ,
               PYTHONPATH=os.pathsep.join(filter(None, [str(ROOT / "src"), os.environ.get("PYTHONPATH")])),
               OMEGA_groundingRemember="disabled",
               OMEGA_GROUNDING_MODE="replay",
               OMEGA_GROUNDING_CASSETTE=str(ROOT / "benchmark" / "cassettes" / "sources.json"))
    runner = os.environ.get("PETTA_RUN", str(Path(PETTA) / "run.sh"))
    run = subprocess.run(["sh", runner, str(program)], cwd=PETTA, env=env,
                         capture_output=True, text=True, timeout=600)
    out = re.sub(r"\x1b\[[0-9;]*m", "", run.stdout + run.stderr)  # PeTTa colours its output
    # PeTTa also echoes compiled source; keep only the lines the program printed.
    printed = [line for line in out.splitlines() if line.startswith(("(loaded ", "(skills ", "(result "))]
    assert "(loaded ())" in printed, out
    assert any('(ground "' in line for line in printed if line.startswith("(skills ")), out
    results = [line for line in printed if line.startswith("(result ")]
    assert len(results) == 4, out  # exactly one result per call, also with lib_patrick loaded
    assert "(grounded CORRECTED ((--> dolphin mammal) (stv 1.0 0.7)) ACT" in results[0]
    assert "(grounded CORRECTED ((--> (× usdc 6) decimals) (stv 1.0 0.9)) ACT" in results[1]
    assert "(grounded REFUTES ((--> weth ([] upgradeable))" in results[2] and "HYPOTHESIZE" in results[2]
    assert "(grounded SUPPORTS ((--> whale mammal)" in results[3] and "ACT" in results[3]


FULL_PROGRAM = """
!(import! &self (library lib_import))
!(git-import! "https://github.com/singnet/Omega.git" "" "{repos}")
!(import! &self (library Omega lib_omega))
(= (command-line) ())
!(initConfig)
!(initLogger)
!(println! (loaded (loadMettaPlugin "grounding" "{plugins}/grounding")))
!(println! (definitions (collapse (match &self (= (grounding-tier $x) $body) found))))
!(println! (results (collapse (ground "((--> whale mammal) (stv 1.0 0.9))"))))
"""


def test_plugin_defines_its_rules_once_under_full_lib_omega(tmp_path):
    """Regression: after lib_omega git-imports petta_lib_chromadb, (library Omega X) resolves
    to several spellings of one path, which used to define the rules twice and make `ground`
    return 2^n copies. Needs Omega's Python deps (or tools/agent_run/stubs) importable."""
    program = tmp_path / "omega_full.metta"
    program.write_text(FULL_PROGRAM.format(repos=Path(OMEGA).parent, plugins=Path(OMEGA) / "plugins"))
    stubs = ROOT / "tools" / "agent_run" / "stubs"
    env = dict(os.environ,
               PYTHONPATH=os.pathsep.join(filter(None, [str(stubs), str(ROOT / "src"), os.environ.get("PYTHONPATH")])),
               OMEGA_embeddingprovider="OpenAI",
               OMEGA_groundingRemember="disabled",
               OMEGA_GROUNDING_MODE="replay",
               OMEGA_GROUNDING_CASSETTE=str(ROOT / "benchmark" / "cassettes" / "sources.json"))
    runner = os.environ.get("PETTA_RUN", str(Path(PETTA) / "run.sh"))
    run = subprocess.run(["sh", runner, str(program)], cwd=PETTA, env=env,
                         capture_output=True, text=True, timeout=600)
    out = re.sub(r"\x1b\[[0-9;]*m", "", run.stdout + run.stderr)
    if "ModuleNotFoundError" in out:
        pytest.skip("Omega's Python dependencies (e.g. openai) are not installed for the runner")
    printed = [line for line in out.splitlines() if line.startswith(("(loaded ", "(definitions ", "(results "))]
    assert "(loaded ())" in printed, out
    assert "(definitions (found))" in printed, out
    results = next(line for line in printed if line.startswith("(results "))
    assert results.count("(grounded ") == 1, results
