import asyncio
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import httpx

P = Path(__file__).resolve().parents[1] / 'custom_components/beneylu/api.py'
spec = importlib.util.spec_from_file_location('beneylu_api', P)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)

def test_html_and_signature():
    post = {'id': 'abc', 'content': '<p>Bonjour &amp; merci</p>', 'createdAt': '2026-11-01T10:00:00+00:00',
            'signableFor': [2, 3], 'postSignatures': [{'signedForId': 2}],
            'linkedAudience': {'audience': [{'userId': 2}, {'userId': 3}]}}
    result = api.normalize_post(post, {2: 'Alice', 3: 'Bob'})
    assert result['text'] == 'Bonjour & merci'
    assert result['pending_child_ids'] == [3]
    assert result['children'] == ['Alice', 'Bob']

def test_future_posts_hidden():
    assert not api.is_visible({'createdAt': '2099-01-01T00:00:00+00:00'})

def test_read_only_fetch_and_reauth():
    calls = []
    def handler(request):
        calls.append((request.method, request.url.path))
        path = request.url.path
        if path == '/api/auth/login_check':
            return httpx.Response(200, json={'refresh_token': 'next'}, headers={'set-cookie': 'BEARER=token; Path=/'})
        if path == '/api/auth/users/me':
            return httpx.Response(200, json={'id': 1, 'displayName': 'Parent', 'children': [{'id': 2, 'firstName': 'Alice'}]})
        if path == '/api/family/posts':
            return httpx.Response(200, json={'posts': [], 'totalPages': 1})
        if path == '/api/notification/notifications-in-app':
            return httpx.Response(200, json=[])
        if path == '/api/chat/family/count':
            return httpx.Response(200, json={'count': 3})
        return httpx.Response(404)
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url=api.BASE_URL) as http:
            client = api.BeneyluClient('parent', 'pass', client=http)
            result = await client.fetch()
            assert result['unread'] == 3
            assert result['children'] == {2: 'Alice'}
    asyncio.run(run())
    assert all(method == 'GET' or path == '/api/auth/login_check' for method, path in calls)
