import math
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

router = APIRouter()
_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=select_autoescape(["html"]),
)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(0, math.ceil(p / 100 * len(ordered)) - 1)
    return ordered[idx]


def build_cost_svg(rows: list[dict], ceiling: float, width: int = 760, height: int = 240) -> str:
    """Cost per PR over time (spec §11) — oldest left, newest right, server-rendered."""
    pad = 40
    if not rows:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
            f'<text x="{width // 2}" y="{height // 2}" text-anchor="middle" '
            f'fill="#888">No reviews yet</text></svg>'
        )
    points = list(reversed(rows))  # recent() is newest-first
    max_y = max(max(float(r["cost_usd"]) for r in points), ceiling, 1e-9) * 1.15
    step = (width - 2 * pad) / max(len(points) - 1, 1)

    def x(i: int) -> float:
        return pad + i * step

    def y(cost: float) -> float:
        return height - pad - (cost / max_y) * (height - 2 * pad)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'font-family="system-ui" font-size="11">'
    ]
    cy = y(ceiling)
    parts.append(
        f'<line x1="{pad}" y1="{cy:.1f}" x2="{width - pad}" y2="{cy:.1f}" '
        f'stroke="#d33" stroke-dasharray="6 4"/>'
        f'<text x="{width - pad}" y="{cy - 5:.1f}" text-anchor="end" fill="#d33">'
        f"ceiling ${ceiling:.2f}</text>"
    )
    if len(points) > 1:
        path = " ".join(f"{x(i):.1f},{y(float(r['cost_usd'])):.1f}" for i, r in enumerate(points))
        parts.append(f'<polyline points="{path}" fill="none" stroke="#36c" stroke-width="2"/>')
    for i, r in enumerate(points):
        px, py = x(i), y(float(r["cost_usd"]))
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="#36c"/>')
        parts.append(
            f'<text x="{px:.1f}" y="{py - 9:.1f}" text-anchor="middle" fill="#333">'
            f"#{r['pr_number']}</text>"
        )
    parts.append(
        f'<line x1="{pad}" y1="{height - pad}" x2="{width - pad}" y2="{height - pad}" '
        f'stroke="#999"/><text x="{pad}" y="{height - 8}" fill="#666">older → newer</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    deps = request.app.state.deps
    if deps is None:
        return HTMLResponse("review pipeline not configured (missing keys)", status_code=503)
    settings = request.app.state.settings
    rows = await deps.reviews.recent(50)
    for r in rows:
        r["cost_usd"] = float(r["cost_usd"] or 0)
    completed = [r for r in rows if r["status"] == "completed"]
    durations = [float(r["duration_ms"]) for r in completed if r.get("duration_ms")]
    stats = {
        "count": len(rows),
        "total_cost": sum(r["cost_usd"] for r in rows),
        "avg_cost": (sum(r["cost_usd"] for r in completed) / len(completed)) if completed else 0.0,
        "p50_s": percentile(durations, 50) / 1000,
        "p95_s": percentile(durations, 95) / 1000,
    }
    chart = build_cost_svg(completed, settings.cost_ceiling_usd)
    html = _env.get_template("dashboard.html").render(rows=rows, stats=stats, chart_svg=chart)
    return HTMLResponse(html)


@router.get("/healthz")
async def healthz(request: Request) -> JSONResponse:
    db = request.app.state.db
    return JSONResponse({"ok": True, "db": bool(db) and await db.ping()})
