"""Offline checks of verifier artifacts, without running candidate or shipped tests."""
import ast
import importlib.util
from pathlib import Path

root = Path(__file__).parent
spec = importlib.util.spec_from_file_location("requirements", root / "requirements.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ids = {r["requirement_id"] for r in module.ROWS}
tree = ast.parse((root / "probe.py").read_text())
literal_ids = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"check", "expect"} and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
        literal_ids.add("TK1-" + node.args[0].value)
unknown = sorted(literal_ids - ids)
assert not unknown, unknown
assert len(ids) == len(module.ROWS)
assert all(r["verdict"] == "unverified" for r in module.ROWS)
assert all(r["candidate_full_revision"] == "UNASSIGNED" for r in module.ROWS)
# Independent oracle boundary self-checks.
overlap = lambda a, b, c, d: a < d and c < b
assert not overlap(0, 90, 90, 180)
assert overlap(0, 90, 89, 179)
assert not overlap(90, 180, 0, 90)
assert overlap(0, 90, 0, 90)
print(f"Syntax/ID/oracle boundary checks passed: {len(ids)} prepared atomic rows, {len(literal_ids)} literal probe IDs. No candidate checks executed.")
