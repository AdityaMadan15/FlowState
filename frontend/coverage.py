"""Offline SVG coverage map for the ten demo workers.

No tile server and no network access is required: worker latitude/longitude from
`/api/workers` is projected into a fixed frame, so the map renders identically in
a venue with no Wi-Fi. Colour is never the only signal — every marker carries a
text label and the legend spells out each state.
"""

from __future__ import annotations

from html import escape
from typing import Any, Sequence

import streamlit as st

WIDTH = 520
HEIGHT = 520
PAD = 54

GREEN = "#0B6E66"
AMBER = "#9A5B08"
INK = "#0C2430"
LINE = "#E2E7E3"
MUTED = "#63798A"


def _project(workers: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise lat/lng into screen coordinates, preserving aspect ratio."""
    located = []
    for worker in workers:
        try:
            lat = float(worker["lat"])
            lng = float(worker["lng"])
        except (KeyError, TypeError, ValueError):
            continue
        located.append({"worker": worker, "lat": lat, "lng": lng})

    if not located:
        return []

    lats = [item["lat"] for item in located]
    lngs = [item["lng"] for item in located]
    lat_span = max(max(lats) - min(lats), 1e-4)
    lng_span = max(max(lngs) - min(lngs), 1e-4)

    inner_w = WIDTH - 2 * PAD
    inner_h = HEIGHT - 2 * PAD
    scale = min(inner_w / lng_span, inner_h / lat_span)
    offset_x = PAD + (inner_w - lng_span * scale) / 2
    offset_y = PAD + (inner_h - lat_span * scale) / 2
    min_lng, max_lat = min(lngs), max(lats)

    for item in located:
        item["x"] = offset_x + (item["lng"] - min_lng) * scale
        item["y"] = offset_y + (max_lat - item["lat"]) * scale
    return located


def _marker(item: dict[str, Any], selected_id: int | None) -> str:
    worker = item["worker"]
    x, y = item["x"], item["y"]
    paid = worker.get("paid")
    name = str(worker.get("name") or "Worker")
    initial = escape(name[:1].upper() or "W")
    worker_id = worker.get("worker_id")

    if paid is True:
        fill, stroke, text_fill, state = GREEN, GREEN, "#FFFFFF", "payout received"
    else:
        fill, stroke, text_fill, state = "#FFFFFF", AMBER, AMBER, "awaiting payout"

    selection_ring = ""
    if selected_id is not None and worker_id == selected_id:
        selection_ring = (
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="21" fill="none" '
            f'stroke="{INK}" stroke-width="1.5" stroke-dasharray="3 3" opacity="0.55" />'
        )

    return (
        f'<g class="fs-node">'
        f"<title>{escape(name)} — {state}</title>"
        f"{selection_ring}"
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="14" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="1.6" />'
        f'<text x="{x:.1f}" y="{y + 4.4:.1f}" text-anchor="middle" '
        f'font-family="Instrument Sans, Segoe UI, sans-serif" font-size="12" '
        f'font-weight="650" fill="{text_fill}">{initial}</text>'
        f'<text x="{x + 21:.1f}" y="{y + 4:.1f}" text-anchor="start" '
        f'font-family="Instrument Sans, Segoe UI, sans-serif" font-size="11.5" '
        f'fill="{INK}" opacity="0.82">{escape(name)}</text>'
        f"</g>"
    )


def build_svg(workers: Sequence[dict[str, Any]], selected_id: int | None = None) -> str | None:
    """Return the SVG markup, or None when no worker has usable coordinates."""
    located = _project(workers)
    if not located:
        return None

    grid = []
    step = 52
    for x in range(PAD, WIDTH - PAD + 1, step):
        grid.append(
            f'<line x1="{x}" y1="{PAD}" x2="{x}" y2="{HEIGHT - PAD}" stroke="{LINE}" stroke-width="1" />'
        )
    for y in range(PAD, HEIGHT - PAD + 1, step):
        grid.append(
            f'<line x1="{PAD}" y1="{y}" x2="{WIDTH - PAD}" y2="{y}" stroke="{LINE}" stroke-width="1" />'
        )

    centre_x = sum(item["x"] for item in located) / len(located)
    centre_y = sum(item["y"] for item in located) / len(located)
    rings = "".join(
        f'<circle cx="{centre_x:.1f}" cy="{centre_y:.1f}" r="{radius}" fill="none" '
        f'stroke="{GREEN}" stroke-width="1" opacity="0.18" />'
        for radius in (70, 120, 170)
    )

    markers = "".join(_marker(item, selected_id) for item in located)
    paid_count = sum(1 for item in located if item["worker"].get("paid") is True)

    return (
        f'<svg viewBox="0 0 {WIDTH} {HEIGHT}" width="100%" role="img" '
        f'aria-label="Coverage map of {len(located)} workers, {paid_count} with a payout received">'
        f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" rx="16" fill="#FCFDFB" '
        f'stroke="{LINE}" />'
        f"{''.join(grid)}"
        f"{rings}"
        f'<text x="{PAD}" y="30" font-family="IBM Plex Mono, monospace" font-size="10.5" '
        f'letter-spacing="1.4" fill="{MUTED}">MUMBAI COVERAGE ZONE</text>'
        f"{markers}"
        f"</svg>"
    )


def render(workers: Sequence[dict[str, Any]], selected_id: int | None = None) -> None:
    """Render the map plus its text legend."""
    svg = build_svg(workers, selected_id)
    if svg is None:
        st.info(
            "Worker coordinates were not returned by the backend, so the coverage map is unavailable."
        )
        return

    located = _project(workers)
    paid_total = sum(1 for item in located if item["worker"].get("paid") is True)
    awaiting = len(located) - paid_total
    st.markdown(svg, unsafe_allow_html=True)
    st.markdown(
        '<div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:10px;'
        'font-size:12px;color:#63798A">'
        f'<span><span style="display:inline-block;width:9px;height:9px;border-radius:50%;'
        f'background:{GREEN};margin-right:6px"></span>Payout received — {paid_total}</span>'
        f'<span><span style="display:inline-block;width:9px;height:9px;border-radius:50%;'
        f'background:#FFFFFF;border:1.5px solid {AMBER};margin-right:6px"></span>'
        f"Awaiting payout — {awaiting}</span>"
        '<span>Marker letter is the worker initial; simulated coordinates, no live GPS.</span>'
        "</div>",
        unsafe_allow_html=True,
    )
