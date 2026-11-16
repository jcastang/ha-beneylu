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
        if path == '/api/auth/groups':
            return httpx.Response(200, json=[{'id': 4, 'label': 'Classe exemple'}])
        if path == '/api/auth/apps/mine':
            return httpx.Response(200, json=[{'name': 'FAMILY', 'open': True}])
        if path == '/api/family/init':
            return httpx.Response(200, json={'can_view': True})
        if path == '/api/chat/family/init':
            return httpx.Response(200, json={'can_view_conversation': True})
        if path == '/api/notification/notification-groups':
            return httpx.Response(200, json=[])
        if path == '/api/auth/groups/classrooms-and-schools':
            return httpx.Response(200, json=[{'id': 4, 'label': 'CE1'}])
        if path == '/api/auth/users/lookup':
            return httpx.Response(200, json=[])
        if path == '/api/chat/family/conversations':
            return httpx.Response(200, json=[{'id': 'c1', 'title': 'Enseignant'}])
        if path == '/api/family/posts':
            return httpx.Response(200, json={'posts': [{'id': 'demo', 'content': '<p>Exemple fictif</p>',
                'createdAt': '2026-01-01T12:00:00+00:00', 'signableFor': [], 'postSignatures': [],
                'linkedAudience': {'audience': []}, 'postAttachments': [], 'postEmbeds': []}],
                'totalPages': 1})
        if path == '/api/notification/notifications-in-app':
            return httpx.Response(200, json=[])
        if path == '/api/family/posts/demo/replies':
            return httpx.Response(200, json=[{'id': 'reply-demo', 'content': '<p>Réponse fictive</p>',
                                              'createdAt': '2026-01-02T12:00:00+00:00'}])
        if path == '/api/chat/family/count':
            return httpx.Response(200, json={'count': 3})
        return httpx.Response(404)
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url=api.BASE_URL) as http:
            client = api.BeneyluClient('parent', 'pass', client=http)
            result = await client.fetch()
            assert result['unread'] == 3
            assert result['posts'][0]['replies'][0]['text'] == 'Réponse fictive'
            assert result['children'] == {2: 'Alice'}
            assert result['groups'] == {4: 'Classe exemple'}
            assert result['conversations'][0]['title'] == 'Enseignant'\n            assert result['apps'][0]['name'] == 'FAMILY'\n            assert result['family_permissions']['can_view'] is True
    asyncio.run(run())
    assert all(method == 'GET' or path in ('/api/auth/login_check', '/api/auth/users/lookup') for method, path in calls)
