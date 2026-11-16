"""Synthetic contract tests based on observed endpoint SHAPES, never user data."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components/beneylu"
API = (ROOT / "api.py").read_text()
SENSORS = (ROOT / "sensor.py").read_text()

def test_observed_routes_are_used():
    for route in ("/api/family/init", "/api/auth/apps/mine", "/api/auth/groups",
                  "/api/chat/family/init", "/api/notification/notification-groups",
                  "/api/family/posts/", "/replies", "/api/media-library/embeds/"):
        assert route in API

def test_no_media_signed_urls_exposed():
    assert '"media_id": media.get("id")' in API
    assert '"url": media.get("display_url")' not in API
    assert '"download_url":' not in API

def test_sensors_for_new_data():
    for name in ("apps", "replies", "media"):
        assert f'"{name}"' in SENSORS

def test_no_private_fixture():
    for path in (ROOT.parent.parent / "tests").glob("*.json"):
        raise AssertionError(f"Do not commit JSON captured from a private HAR: {path.name}")
