"""Pure FlowState payout, loan, and sweep decision rules."""

from config import (
    AQI_THRESHOLD,
    RAIN_THRESHOLD_MM,
    SURVIVAL_THRESHOLD_INR,
)


def decide_action(
    rain_mm: float, aqi: float, predicted_income: float
) -> dict[str, int | float | str]:
    """Return the demo action and amounts without side effects."""
    shortfall = max(0, SURVIVAL_THRESHOLD_INR - predicted_income)
    loan_amount = 0
    sweep_amount = 0

    if rain_mm > RAIN_THRESHOLD_MM or aqi > AQI_THRESHOLD:
        action = "TRIGGER_PAYOUT"
    elif predicted_income < SURVIVAL_THRESHOLD_INR:
        action = "OFFER_LOAN"
        loan_amount = round(SURVIVAL_THRESHOLD_INR - predicted_income)
    else:
        action = "NONE"

    if predicted_income > 1000:
        sweep_amount = round(predicted_income * 0.10)

    return {
        "action": action,
        "loan_amount": loan_amount,
        "sweep_amount": sweep_amount,
        "shortfall": shortfall,
    }
