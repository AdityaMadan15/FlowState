"""Presentation-only helpers: currency, hashes, labels and status wording.

Nothing here computes business values — every number comes from the API and is
only formatted for display.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

# Action codes returned by the backend decision engine.
ACTION_COPY = {
    "TRIGGER_PAYOUT": "Instant payout",
    "OFFER_LOAN": "Loan offered",
    "NONE": "No action needed",
}

# Badge tone per action: payout is the strongest signal, loan is a caution.
ACTION_TONE = {
    "TRIGGER_PAYOUT": "ok",
    "OFFER_LOAN": "warn",
    "NONE": "idle",
}

SCENARIO_COPY = {
    "clear": "Clear",
    "rainy": "Rainy",
    "storm": "Storm active",
    "unavailable": "Unavailable",
}


def action_label(action: object) -> str:
    """Human label for a backend action code."""
    if action is None:
        return "Not reported"
    return ACTION_COPY.get(str(action), str(action).replace("_", " ").title())


def action_tone(action: object) -> str:
    if action is None:
        return "idle"
    return ACTION_TONE.get(str(action), "idle")


def scenario_label(scenario: object) -> str:
    if not scenario:
        return "Unavailable"
    return SCENARIO_COPY.get(str(scenario), str(scenario).replace("_", " ").title())


def inr(value: object, *, fallback: str = "Unavailable") -> str:
    """Format an API-supplied rupee amount with Indian digit grouping."""
    if value is None or isinstance(value, bool):
        return fallback
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return fallback
    if amount == amount.to_integral_value():
        body = f"{int(amount):,}"
    else:
        body = f"{amount.quantize(Decimal('0.1')):,}"
    return f"\u20b9{body}"


def number(value: object, *, fallback: str = "—") -> str:
    """Format a plain API number (non-currency), e.g. rain mm or AQI."""
    if value is None or isinstance(value, bool):
        return fallback
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def short_hash(value: object, *, head: int = 10, tail: int = 8) -> str:
    """Middle-truncate a transaction hash or address for table display."""
    text = str(value or "").strip()
    if not text:
        return "Not reported"
    if len(text) <= head + tail + 3:
        return text
    return f"{text[:head]}…{text[-tail:]}"


def short_address(value: object) -> str:
    return short_hash(value, head=8, tail=6)


def status_text(value: object, *, yes: str = "Connected", no: str = "Unavailable") -> str:
    """Tri-state wording for boolean health fields: never guess a healthy state."""
    if value is True:
        return yes
    if value is False:
        return no
    return "Not reported"


def status_tone(value: object) -> str:
    if value is True:
        return "ok"
    if value is False:
        return "bad"
    return "idle"


def payout_mode(mock: object) -> tuple[str, str]:
    """(label, tone) for the mock / on-chain distinction."""
    if mock is True:
        return "Mock transfer", "warn"
    if mock is False:
        return "On-chain", "ok"
    return "Mode not reported", "idle"


def paid_label(paid: object) -> str:
    if paid is True:
        return "Payout received"
    if paid is False:
        return "Awaiting payout"
    return "Status not reported"


def paid_tone(paid: object) -> str:
    if paid is True:
        return "ok"
    if paid is False:
        return "idle"
    return "idle"


def source_label(source: object) -> str:
    """Prediction source: trained model vs deterministic formula fallback."""
    mapping = {"model": "LightGBM model", "fallback": "Formula fallback"}
    if source is None:
        return "Not reported"
    return mapping.get(str(source), str(source).title())
