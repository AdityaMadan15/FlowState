"""Reusable presentation primitives for the FlowState dashboard.

Everything here returns or renders markup only — no API calls, no business rules.
"""

from __future__ import annotations

from html import escape
from typing import Sequence

import streamlit as st

TONES = {"ok", "warn", "bad", "idle", "outline"}


def render(markup: str) -> None:
    """Render a raw HTML fragment."""
    st.markdown(markup, unsafe_allow_html=True)


def badge(text: object, tone: str = "idle", dot: bool = True) -> str:
    """A status pill. Colour is always paired with written text."""
    cls = tone if tone in TONES else "idle"
    dot_html = '<span class="dot"></span>' if dot else ""
    return f'<span class="fs-badge fs-badge--{cls}">{dot_html}{escape(str(text))}</span>'


def page_header(eyebrow: str, title: str, subtitle: str, chips: Sequence[str] = ()) -> None:
    """Consistent page top: eyebrow, serif headline, one-sentence descriptor."""
    chip_row = ""
    if chips:
        chip_row = (
            '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:16px">'
            + "".join(chips)
            + "</div>"
        )
    render(
        f'<div class="fs-page-head">'
        f'<div class="fs-eyebrow">{escape(eyebrow)}</div>'
        f'<h1 class="fs-page-title">{escape(title)}</h1>'
        f'<p class="fs-page-sub">{escape(subtitle)}</p>'
        f"{chip_row}</div>"
    )


def section(title: str, meta: str | None = None) -> None:
    """Section label with an optional right-aligned annotation."""
    meta_html = f'<span class="fs-section-meta">{escape(meta)}</span>' if meta else ""
    render(
        f'<div class="fs-section">'
        f'<h2 class="fs-section-title">{escape(title)}</h2>'
        f"{meta_html}</div>"
    )


def stat_tile(
    label: str,
    value: str,
    meta: str | None = None,
    small: bool = False,
    badge_text: str | None = None,
    badge_tone: str = "idle",
) -> str:
    """Reusable KPI card; all displayed values are formatted by the caller."""
    size_class = " fs-stat-value--sm" if small or len(value) > 12 else ""
    meta_html = (
        f'<div class="fs-stat-meta">{escape(meta)}</div>' if meta else ""
    )
    badge_html = (
        f'<div class="fs-stat-badge">{badge(badge_text, badge_tone)}</div>'
        if badge_text
        else ""
    )
    return (
        f'<div class="fs-stat">'
        f'<div class="fs-stat-top"><div class="fs-stat-label">{escape(label)}</div>{badge_html}</div>'
        f'<div class="fs-stat-value{size_class}">{escape(value)}</div>'
        f"{meta_html}</div>"
    )


def stat_row(tiles: Sequence[dict[str, object]]) -> None:
    """Lay tiles out in equal columns. Each dict: label, value, optional meta/small."""
    if not tiles:
        return
    columns = st.columns(len(tiles), gap="small")
    for column, tile in zip(columns, tiles):
        with column:
            render(
                stat_tile(
                    str(tile.get("label", "")),
                    str(tile.get("value", "—")),
                    tile.get("meta") or None,  # type: ignore[arg-type]
                    bool(tile.get("small", False)),
                    str(tile["badge"]) if tile.get("badge") is not None else None,
                    str(tile.get("tone", "idle")),
                )
            )


def footer() -> None:
    """Shared product footer for page views."""
    render(
        '<footer class="fs-footer">'
        '<span>FlowState</span>'
        '<span>Built for gig workers</span>'
        '</footer>'
    )


def kv_table(pairs: Sequence[tuple[str, str]]) -> str:
    """Two-column definition list styled as a card body."""
    rows = "".join(
        f'<div class="fs-kv"><dt>{escape(key)}</dt><dd>{escape(value)}</dd></div>'
        for key, value in pairs
    )
    return rows


def card(body: str, title: str | None = None, note: str | None = None) -> str:
    """A static card. For cards containing widgets use st.container(border=True)."""
    head = ""
    if title:
        head += f'<div class="fs-card-title">{escape(title)}</div>'
    if note:
        head += f'<p class="fs-card-note">{escape(note)}</p>'
    return f'<div class="fs-card">{head}<div style="margin-top:12px">{body}</div></div>'


def empty_state(message: str, hint: str | None = None) -> None:
    hint_html = (
        f'<div style="margin-top:6px;font-size:12.5px;color:#8A9BA5">{escape(hint)}</div>'
        if hint
        else ""
    )
    render(f'<div class="fs-empty">{escape(message)}{hint_html}</div>')


def reasons_chips(reasons: Sequence[str]) -> str:
    """Render SHAP/model reasons exactly as the API supplied them."""
    if not reasons:
        return ""
    chips = "".join(f'<span class="fs-reason">{escape(str(r))}</span>' for r in reasons)
    return f'<div class="fs-reasons">{chips}</div>'


def bar_chart(
    rows: Sequence[tuple[str, float, bool]],
    ceiling: float,
    marker: float,
) -> str:
    """Horizontal bars for predicted income against a reference marker.

    rows: (label, value, is_below_marker). Values are API numbers, unmodified.
    """
    if not rows:
        return '<div class="fs-empty">No predictions to compare.</div>'
    span = max(ceiling, marker, 1.0)
    marker_pct = min(100.0, max(0.0, marker / span * 100.0))
    items = []
    for label, value, low in rows:
        width = min(100.0, max(1.0, value / span * 100.0))
        fill_class = " fs-bar-fill--low" if low else ""
        items.append(
            f'<div class="fs-bar-row">'
            f'<div class="fs-bar-name">{escape(label)}</div>'
            f'<div class="fs-bar-track">'
            f'<div class="fs-bar-fill{fill_class}" style="width:{width:.2f}%"></div>'
            f'<div class="fs-bar-marker" style="left:{marker_pct:.2f}%"></div>'
            f"</div>"
            f'<div class="fs-bar-value">{escape(_format_plain(value))}</div>'
            f"</div>"
        )
    return f'<div class="fs-bars">{"".join(items)}</div>'


def _format_plain(value: float) -> str:
    return f"\u20b9{value:,.1f}" if value % 1 else f"\u20b9{value:,.0f}"


def flow_steps(steps: Sequence[tuple[str, str, str]]) -> str:
    """Numbered pipeline strip: (index, title, detail)."""
    cards = "".join(
        f'<div class="fs-flow-step">'
        f'<div class="fs-flow-index">{escape(index)}</div>'
        f"<b>{escape(title)}</b>"
        f"<span>{escape(detail)}</span></div>"
        for index, title, detail in steps
    )
    return f'<div class="fs-flow">{cards}</div>'
