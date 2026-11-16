import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components/beneylu"

def functions_from(path, names):
    tree = ast.parse((ROOT / path).read_text())
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    namespace = {}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(ROOT / path), "exec"), namespace)
    return namespace

def test_latest_post_is_newest():
    fn = functions_from("sensor.py", {"latest_post"})["latest_post"]
    assert fn([{"date": "2026-11-01", "id": "old"}, {"date": "2026-11-15", "id": "new"}])["id"] == "new"
    assert fn([]) is None

def test_latest_notification_is_newest():
    fn = functions_from("sensor.py", {"latest_notification"})["latest_notification"]
    assert fn([{"date": "2026-11-01", "id": 1}, {"date": "2026-11-15", "id": 2}])["id"] == 2
    assert fn([]) is None
