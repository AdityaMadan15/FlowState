"""Train FlowState's deterministic demo income model and SHAP explainer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
from lightgbm import LGBMRegressor


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "model.joblib"
EXPLAINER_PATH = MODEL_DIR / "explainer.joblib"

FEATURES = [
    "historical_daily_earnings",
    "day_of_week",
    "rain_mm",
    "aqi",
]
RANDOM_SEED = 42
DAYS_PER_WORKER = 120
DEMO_DAY_OF_WEEK = 2  # Monday=0, so the fixed demo day is Wednesday.

# Simulated for the demo: earnings and weather are synthetic. The prediction
# pipeline and SHAP explanations are real; payouts run only on the local chain.
WORKERS = [
    {"worker_id": 1, "name": "Ravi", "baseline": 850},
    {"worker_id": 2, "name": "Amit", "baseline": 780},
    {"worker_id": 3, "name": "Suresh", "baseline": 900},
    {"worker_id": 4, "name": "Imran", "baseline": 700},
    {"worker_id": 5, "name": "Deepak", "baseline": 950},
    {"worker_id": 6, "name": "Manoj", "baseline": 820},
    {"worker_id": 7, "name": "Sanjay", "baseline": 760},
    {"worker_id": 8, "name": "Vikram", "baseline": 880},
    {"worker_id": 9, "name": "Arjun", "baseline": 640},
    {"worker_id": 10, "name": "Karan", "baseline": 990},
]

SCENARIOS = {
    "clear": {"rain_mm": 5, "aqi": 120},
    "rainy": {"rain_mm": 45, "aqi": 250},
    "storm": {"rain_mm": 80, "aqi": 450},
}


def predict_income_formula(
    baseline: float, day_of_week: int, rain_mm: float, aqi: float
) -> float:
    """Fallback-compatible income formula, before synthetic noise is added."""
    rain_factor = max(0.0, 1.0 - 0.0085 * rain_mm)
    aqi_factor = max(0.0, 1.0 - 0.0008 * max(aqi - 150.0, 0.0))
    weekend_boost = 1.15 if day_of_week in (5, 6) else 1.0
    income = baseline * rain_factor * aqi_factor * weekend_boost
    return max(0.0, income)


def generate_synthetic_data() -> pd.DataFrame:
    """Create 10 workers x 120 days with exactly 20% severe weather rows."""
    rng = np.random.default_rng(RANDOM_SEED)
    records: list[dict[str, float | int]] = []

    for worker in WORKERS:
        severe_indices = set(
            rng.choice(DAYS_PER_WORKER, size=DAYS_PER_WORKER // 5, replace=False)
            .astype(int)
            .tolist()
        )
        severe_rain_indices = set(
            rng.choice(sorted(severe_indices), size=len(severe_indices) // 2, replace=False)
            .astype(int)
            .tolist()
        )

        for day_index in range(DAYS_PER_WORKER):
            day_of_week = int(rng.integers(0, 7))
            if day_index in severe_rain_indices:
                rain_mm = float(rng.uniform(51, 100))
                aqi = float(rng.uniform(50, 400))
            elif day_index in severe_indices:
                rain_mm = float(rng.uniform(0, 50))
                aqi = float(rng.uniform(401, 500))
            else:
                rain_mm = float(rng.uniform(0, 50))
                aqi = float(rng.uniform(50, 400))

            expected_income = predict_income_formula(
                worker["baseline"], day_of_week, rain_mm, aqi
            )
            actual_income = max(0.0, expected_income + float(rng.normal(0, 30)))
            records.append(
                {
                    "worker_id": worker["worker_id"],
                    "day_of_week": day_of_week,
                    "historical_daily_earnings": worker["baseline"],
                    "rain_mm": rain_mm,
                    "aqi": aqi,
                    "actual_income": actual_income,
                }
            )

    return pd.DataFrame.from_records(records)


def _shap_vector(explainer: Any, feature_row: pd.DataFrame) -> np.ndarray:
    """Normalize SHAP's regression output to one value per feature."""
    values = explainer.shap_values(feature_row)
    if isinstance(values, list):
        values = values[0]
    values = np.asarray(values)
    if values.ndim == 2:
        values = values[0]
    return values


def _rain_label(rain_mm: float) -> str:
    if rain_mm >= 50:
        return "Heavy rain"
    if rain_mm >= 20:
        return "Moderate rain"
    return "Light rain"


def _aqi_label(aqi: float) -> str:
    if aqi >= 400:
        return "Severe AQI"
    if aqi >= 200:
        return "Poor AQI"
    return "Mild AQI"


def get_weather_reasons(
    explainer: Any, feature_row: pd.DataFrame, top_n: int = 2
) -> list[str]:
    """Return the most negative weather-only SHAP reasons for one prediction."""
    if len(feature_row) != 1:
        raise ValueError("feature_row must contain exactly one worker prediction")

    shap_values = _shap_vector(explainer, feature_row)
    feature_positions = {name: index for index, name in enumerate(FEATURES)}
    rain_mm = float(feature_row.iloc[0]["rain_mm"])
    aqi = float(feature_row.iloc[0]["aqi"])
    candidates: list[tuple[float, str]] = []

    for feature_name, value, label, measured in (
        ("rain_mm", rain_mm, _rain_label(rain_mm), f"{rain_mm:g}mm"),
        ("aqi", aqi, _aqi_label(aqi), f"{aqi:g}"),
    ):
        contribution = float(shap_values[feature_positions[feature_name]])
        if contribution <= -1.0:
            rupee_loss = int(round(abs(contribution)))
            candidates.append(
                (contribution, f"{label} ({measured}): -₹{rupee_loss}")
            )

    candidates.sort(key=lambda item: item[0])
    reasons = [text for _, text in candidates[:top_n]]
    return reasons or ["Normal conditions: no income drop expected"]


def build_model() -> tuple[LGBMRegressor, shap.TreeExplainer, pd.DataFrame]:
    """Train LightGBM and construct its TreeExplainer from synthetic rows."""
    data = generate_synthetic_data()
    features = data[FEATURES]
    target = data["actual_income"]

    model = LGBMRegressor(
        n_estimators=200,
        learning_rate=0.05,
        min_child_samples=5,
        random_state=RANDOM_SEED,
        n_jobs=1,
        verbosity=-1,
    )
    model.fit(features, target)
    explainer = shap.TreeExplainer(model)
    return model, explainer, data


def _self_check(model: LGBMRegressor) -> None:
    print("Self-check predictions (Wednesday; INR):")
    print(f"{'Worker':<10} {'Clear':>10} {'Rainy':>10} {'Storm':>10}")

    predictions: dict[str, list[float]] = {name: [] for name in SCENARIOS}
    for worker in WORKERS:
        row_predictions: dict[str, float] = {}
        for scenario_name, weather in SCENARIOS.items():
            row = pd.DataFrame(
                [
                    {
                        "historical_daily_earnings": worker["baseline"],
                        "day_of_week": DEMO_DAY_OF_WEEK,
                        "rain_mm": weather["rain_mm"],
                        "aqi": weather["aqi"],
                    }
                ],
                columns=FEATURES,
            )
            prediction = max(0.0, float(model.predict(row)[0]))
            predictions[scenario_name].append(prediction)
            row_predictions[scenario_name] = prediction

        print(
            f"{worker['name']:<10} "
            f"{row_predictions['clear']:>10.1f} "
            f"{row_predictions['rainy']:>10.1f} "
            f"{row_predictions['storm']:>10.1f}"
        )

    assert all(value < 500 for value in predictions["storm"]), (
        "Self-check failed: every storm prediction must be below ₹500. "
        "Check the income formula and weather coverage in the training data."
    )
    assert all(value > 500 for value in predictions["clear"]), (
        "Self-check failed: every clear prediction must be above ₹500. "
        "Check the clear scenario and worker baselines."
    )


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model, explainer, data = build_model()
    joblib.dump(model, MODEL_PATH)
    joblib.dump(explainer, EXPLAINER_PATH)

    severe = (data["rain_mm"] > 50) | (data["aqi"] > 400)
    print(
        f"Trained on {len(data)} rows; severe-weather rows: "
        f"{int(severe.sum())}/{len(data)} ({severe.mean():.1%})."
    )
    print(f"Saved model: {MODEL_PATH}")
    print(f"Saved explainer: {EXPLAINER_PATH}")
    _self_check(model)


if __name__ == "__main__":
    main()
