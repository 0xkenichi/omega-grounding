import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "agent_run"))
from agentrun_guard import allowed_inference  # noqa: E402


def test_accepts_inference():
    assert allowed_inference("(|- ((--> a b) (stv 1.0 0.9)) ((--> b c) (stv 1.0 0.9)))")
    assert allowed_inference("(|~ ((Implication (Inheritance $1 (IntSet Feathered)) (Inheritance $1 Bird)) (stv 1.0 0.9)))")
    assert allowed_inference("(|- ((--> (× usdc 6) decimals) (stv 1.0 0.9)))")


def test_rejects_code_smuggled_into_premises():
    for bad in [
        '(|- ((--> a b) (stv 1.0 0.9)) (py-call (os.system "rm -rf ~")))',
        '(|- ((--> (shell "ls") b) (stv 1.0 0.9)))',
        '(|- (import! &self ./evil))',
        '(py-call (os.getcwd))',
        '(--> a b)',
        '(|- ((--> a b) (stv 1.0 0.9))',
        '(|- (eval (shell "id")))',
    ]:
        assert not allowed_inference(bad), bad
