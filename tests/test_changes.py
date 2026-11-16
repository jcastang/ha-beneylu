import ast
from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'custom_components/beneylu/coordinator.py'
module = ast.parse(p.read_text())
selected = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name in {'fingerprint', 'changes'}]
namespace = {'hashlib': __import__('hashlib'), 'json': __import__('json')}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(p), 'exec'), namespace)

def test_change_detection():
    post = {'id': 'p1', 'text': 'A', 'pending_child_ids': [2]}
    seen, changed = namespace['changes']({}, [post], [])
    assert changed == ['post:p1']
    _, changed = namespace['changes'](seen, [post], [])
    assert changed == []
    post['pending_child_ids'] = []
    _, changed = namespace['changes'](seen, [post], [])
    assert changed == ['post:p1']
