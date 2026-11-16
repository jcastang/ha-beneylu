"""Async read-only Beneylu client, based on API behavior in hclaria/beneylu-mcp."""
from __future__ import annotations
import asyncio
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
import httpx

BASE_URL = "https://school.beneylu.com"

class BeneyluError(Exception):
    """Beneylu request failure."""

class BeneyluAuthError(BeneyluError):
    """Beneylu authentication failure."""

class _Strip(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in {"p", "div", "br", "li", "tr"}:
            self.parts.append("\n")
    def handle_data(self, data):
        self.parts.append(data)

def html_to_text(value):
    parser = _Strip()
    parser.feed(value or "")
    return "\n".join(x.strip() for x in "".join(parser.parts).splitlines() if x.strip())

def normalize_post(raw, children, base_url=BASE_URL):
    ids = {int(a["userId"]) for a in (raw.get("linkedAudience") or {}).get("audience", []) if "userId" in a}
    signed = {int(s["signedForId"]) for s in raw.get("postSignatures") or [] if s.get("signedForId") is not None}
    pending = {int(x) for x in raw.get("signableFor") or []} - signed
    date = raw.get("visibleAt") or raw.get("createdAt")
    return {
        "id": str(raw["id"]), "date": date, "text": html_to_text(raw.get("content")),
        "child_ids": sorted(ids), "children": [children.get(i, str(i)) for i in sorted(ids)],
        "pending_child_ids": sorted(pending), "signature_required": bool(raw.get("signableFor")),
        "pending_signature_for": [children.get(i, str(i)) for i in sorted(pending)],
        "url": f"{base_url}/family-information/{raw['id']}",
        "attachments": len(raw.get("postAttachments") or []) + len(raw.get("postEmbeds") or []),
    }

def is_visible(raw, now=None):
    now = now or datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(raw.get("visibleAt") or raw["createdAt"]) <= now
    except (ValueError, KeyError, TypeError):
        return False

class BeneyluClient:
    def __init__(self, username, password, refresh_token=None, client=None):
        self.username, self.password = username, password
        self.refresh_token = refresh_token
        self.http = client or httpx.AsyncClient(base_url=BASE_URL, timeout=20, follow_redirects=False,
                                                 headers={"X-Requested-With": "XMLHttpRequest"})
        self._owns_client = client is None
        self._lock = asyncio.Lock()
        self._last_login = None

    async def close(self):
        if self._owns_client:
            await self.http.aclose()

    async def _send(self, method, path, **kwargs):
        try:
            return await self.http.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise BeneyluError(f"Network error: {type(exc).__name__}") from exc

    async def _open_session(self):
        if self.refresh_token:
            response = await self._send("POST", "/api/auth/token/refresh", json={"refresh_token": self.refresh_token})
            if response.status_code == 200 and "BEARER" in self.http.cookies:
                self.refresh_token = response.json().get("refresh_token") or self.refresh_token
                return
            if response.status_code not in (400, 401, 403):
                raise BeneyluError(f"Token refresh failed: HTTP {response.status_code}")
            self.refresh_token = None
        if not self.username or not self.password:
            raise BeneyluAuthError("A valid refresh token or username and password are required")
        now = datetime.now(timezone.utc)
        if self._last_login and now - self._last_login < timedelta(hours=1):
            raise BeneyluAuthError("Login retry limited to once per hour")
        self._last_login = now
        response = await self._send("POST", "/api/auth/login_check", json={
            "login": self.username, "password": self.password, "otp": "", "remember_me": True, "captcha": ""})
        if response.status_code == 200 and "BEARER" in self.http.cookies:
            try:
                self.refresh_token = response.json().get("refresh_token") or self.refresh_token
            except (ValueError, AttributeError):
                pass
            return
        if "X-Bns-Captcha" in response.headers:
            raise BeneyluAuthError("Captcha required: obtain a refresh token using the browser")
        raise BeneyluAuthError(f"Login failed: HTTP {response.status_code} (OTP may be required)")

    async def get(self, path, params=None):
        async with self._lock:
            if "BEARER" not in self.http.cookies:
                await self._open_session()
            response = await self._send("GET", path, params=params)
            if response.status_code == 401:
                self.http.cookies.clear()
                await self._open_session()
                response = await self._send("GET", path, params=params)
            if response.status_code == 401:
                raise BeneyluAuthError("Session rejected")
            if response.status_code >= 400:
                raise BeneyluError(f"HTTP {response.status_code}: {path}")
            try:
                return response.json()
            except ValueError as exc:
                raise BeneyluError("Invalid JSON response") from exc

    async def fetch(self, max_pages=5):
        me = await self.get("/api/auth/users/me") or {}
        children = {int(c["id"]): c.get("firstName") or str(c["id"]) for c in me.get("children") or []}
        posts = []
        for page in range(1, max_pages + 1):
            result = await self.get("/api/family/posts", {"page": page, "status": "published"}) or {}
            posts.extend(normalize_post(raw, children) for raw in result.get("posts") or [] if is_visible(raw))
            if page >= int(result.get("totalPages") or 1):
                break
        notifications = await self.get("/api/notification/notifications-in-app") or []
        count = await self.get("/api/chat/family/count")
        unread = count.get("count", 0) if isinstance(count, dict) else count
        try:
            unread = int(unread or 0)
        except (TypeError, ValueError):
            unread = 0
        return {"account": me.get("displayName") or self.username or "Beneylu",
                "children": children, "posts": posts, "notifications": notifications,
                "unread": unread}
