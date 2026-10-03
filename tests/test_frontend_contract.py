import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frontend_exposes_aligned_workflows_and_pwa_assets():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    required_routes = [
        "/profile/trainee",
        "/my/course-enrollments",
        "/attendance/qr-token",
        "/attendance/scan",
        "/offline/sync",
        "/career/chat",
        "/analytics/overview",
        "/hostel/rooms",
        "/hostel/allocations",
        "/logistics",
        "/ai/recommendations",
        "/ai/risk-insights",
        "/devices",
    ]
    for route in required_routes:
        assert route in html

    assert 'navigator.serviceWorker.register("./sw.js")' in html
    assert 'rel="manifest" href="./manifest.webmanifest"' in html
    manifest = json.loads((ROOT / "frontend" / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["display"] == "standalone"
    assert manifest["start_url"] == "./index.html"
    assert "sahakarsetu-shell" in (ROOT / "frontend" / "sw.js").read_text(encoding="utf-8")
