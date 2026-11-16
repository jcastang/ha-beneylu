import ast
from pathlib import Path

API = Path(__file__).resolve().parents[1] / "custom_components/beneylu/api.py"
SOURCE = API.read_text()

def test_read_only_endpoints():
    assert '/api/chat/family/conversations' in SOURCE
    assert '/api/auth/groups/classrooms-and-schools' in SOURCE
    assert '/api/auth/users/lookup' in SOURCE
    assert '/api/family/posts' in SOURCE
    assert '/api/notification/notifications-in-app' in SOURCE
    assert '/api/chat/family/count' in SOURCE

def test_conversation_content_not_polled():
    tree = ast.parse(SOURCE)
    client = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'BeneyluClient')
    fetch = next(n for n in client.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'fetch')
    assert 'get_conversation(' not in ast.get_source_segment(SOURCE, fetch)
    assert 'list_conversations(' in ast.get_source_segment(SOURCE, fetch)

def test_post_metadata_present():
    assert '"author":' in SOURCE
    assert '"groups":' in SOURCE
    assert '"signatures":' in SOURCE
    assert '"replies_allowed":' in SOURCE
