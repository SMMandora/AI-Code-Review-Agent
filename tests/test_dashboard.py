import asyncio

from fastapi.testclient import TestClient

from codereview.settings import Settings
from codereview.stores import ReviewRecord
from codereview.web.app import create_app
from codereview.web.dashboard import build_cost_svg, percentile


def test_percentile():
    assert percentile([], 95) == 0.0
    assert percentile([10.0], 95) == 10.0
    vals = [float(i) for i in range(1, 101)]
    assert percentile(vals, 50) == 50.0
    assert percentile(vals, 95) == 95.0


def test_build_cost_svg_contains_points_and_ceiling():
    rows = [
        {"pr_number": 7, "cost_usd": 0.12, "created_at": None},
        {"pr_number": 8, "cost_usd": 0.34, "created_at": None},
    ]
    svg = build_cost_svg(rows, ceiling=0.50)
    assert svg.startswith("<svg")
    assert svg.count("<circle") == 2
    assert "#7" in svg and "#8" in svg
    assert "ceiling" in svg


def test_build_cost_svg_empty():
    svg = build_cost_svg([], ceiling=0.50)
    assert "No reviews yet" in svg


def test_dashboard_page_renders_rows(settings):
    app = create_app(settings)
    with TestClient(app) as client:
        store = app.state.deps.reviews
        asyncio.run(store.record(ReviewRecord(
            repo="acme/widgets", pr_number=7, head_sha="abcdef1234567890",
            status="completed", trigger="webhook", model="claude-sonnet-4-6",
            findings_total=4, comments_posted=3, input_tokens=9000,
            output_tokens=1200, cost_usd=0.045, duration_ms=14200,
        )))
        asyncio.run(store.record(ReviewRecord(
            repo="acme/widgets", pr_number=8, head_sha="1234567890abcdef",
            status="cost_exceeded", trigger="slash", model="claude-sonnet-4-6",
        )))
        r = client.get("/")
        assert r.status_code == 200
        html = r.text
        assert "#7" in html and "abcdef1" in html
        assert "cost_exceeded" in html
        assert "$0.0450" in html
        assert "<svg" in html


def test_dashboard_503_without_deps():
    app = create_app(Settings(_env_file=None))  # no keys -> no deps
    with TestClient(app) as client:
        assert client.get("/").status_code == 503
