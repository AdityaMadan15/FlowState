"""FlowState FastAPI backend: model predictions and demo API stubs."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:  # Support both `uvicorn main:app` from backend/ and `backend.main:app`.
    from .blockchain import chain_connected, trigger_payout
    from .config import DEMO_DAY_OF_WEEK, PAYOUT_INR, SCENARIOS, WORKERS
    from .decision import decide_action
    from .train_model import (
        FEATURES,
        EXPLAINER_PATH,
        MODEL_PATH,
        get_weather_reasons,
        predict_income_formula,
    )
except ImportError:
    from blockchain import chain_connected, trigger_payout
    from config import DEMO_DAY_OF_WEEK, PAYOUT_INR, SCENARIOS, WORKERS
    from decision import decide_action
    from train_model import (
        FEATURES,
        EXPLAINER_PATH,
        MODEL_PATH,
        get_weather_reasons,
        predict_income_formula,
    )


logger = logging.getLogger(__name__)
app = FastAPI(title="FlowState Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATE_LOCK = threading.Lock()
ACTION_LOCK = threading.Lock()
STATE: dict[str, Any] = {
    "scenario": "clear",
    "ledger": {
        worker["worker_id"]: {
            "balance_inr": 1200,
            "vault_inr": 300,
            "loan_outstanding_inr": 0,
            "paid": False,
            "last_payout_tx": None,
        }
        for worker in WORKERS
    },
    "payout_log": [],
}

MODEL: Any | None = None
EXPLAINER: Any | None = None


def load_model_assets() -> None:
    """Load model assets once; missing or invalid files select formula fallback."""
    global MODEL, EXPLAINER
    try:
        MODEL = joblib.load(MODEL_PATH)
        EXPLAINER = joblib.load(EXPLAINER_PATH)
        logger.info("Loaded prediction model and SHAP explainer")
    except Exception:
        MODEL = None
        EXPLAINER = None
        logger.exception("Model assets unavailable; using formula predictor")


@app.on_event("startup")
def startup() -> None:
    load_model_assets()


def _worker_config(worker_id: int) -> dict[str, Any]:
    for worker in WORKERS:
        if worker["worker_id"] == worker_id:
            return worker
    raise HTTPException(status_code=404, detail=f"Worker {worker_id} not found")


def _worker_response(worker_id: int) -> dict[str, Any]:
    worker = _worker_config(worker_id)
    with STATE_LOCK:
        ledger = dict(STATE["ledger"][worker_id])
    return {
        "worker_id": worker_id,
        "name": worker["name"],
        "balance_inr": ledger["balance_inr"],
        "vault_inr": ledger["vault_inr"],
        "loan_outstanding_inr": ledger["loan_outstanding_inr"],
        "last_payout_tx": ledger["last_payout_tx"],
    }


def _feature_row(worker: dict[str, Any], weather: dict[str, float]) -> pd.DataFrame:
    return pd.DataFrame(
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


def _fallback_reasons(baseline: float, rain_mm: float, aqi: float) -> list[str]:
    rain_factor = 1.0 - 0.0085 * rain_mm
    aqi_factor = 1.0 - 0.0008 * max(aqi - 150, 0)
    contributions = [
        ("rain_mm", baseline * (1.0 - rain_factor)),
        ("aqi", baseline * rain_factor * (1.0 - aqi_factor)),
    ]

    def label(feature: str, value: float) -> str:
        if feature == "rain_mm":
            return "Heavy rain" if value >= 50 else "Moderate rain" if value >= 20 else "Light rain"
        return "Severe AQI" if value >= 400 else "Poor AQI" if value >= 200 else "Mild AQI"

    reasons: list[tuple[float, str]] = []
    for feature, loss in contributions:
        if loss >= 1.0:
            value = rain_mm if feature == "rain_mm" else aqi
            measured = f"{value:g}mm" if feature == "rain_mm" else f"{value:g}"
            reasons.append(
                (loss, f"{label(feature, value)} ({measured}): -₹{round(loss)}")
            )
    reasons.sort(key=lambda item: item[0], reverse=True)
    return [text for _, text in reasons[:2]] or [
        "Normal conditions: no income drop expected"
    ]


def _predict(worker: dict[str, Any], scenario: str) -> dict[str, Any]:
    weather = {"scenario": scenario, **SCENARIOS[scenario]}
    feature_row = _feature_row(worker, weather)
    source = "model"

    try:
        if MODEL is None or EXPLAINER is None:
            raise RuntimeError("Model or SHAP explainer is not loaded")
        predicted_income = max(0.0, float(MODEL.predict(feature_row)[0]))
        reasons = get_weather_reasons(EXPLAINER, feature_row)
    except Exception:
        source = "fallback"
        predicted_income = predict_income_formula(
            worker["baseline"],
            DEMO_DAY_OF_WEEK,
            weather["rain_mm"],
            weather["aqi"],
        )
        reasons = _fallback_reasons(
            worker["baseline"], weather["rain_mm"], weather["aqi"]
        )
        logger.exception("Prediction used formula fallback for worker %s", worker["worker_id"])

    decision = decide_action(
        weather["rain_mm"], weather["aqi"], predicted_income
    )
    return {
        "worker_id": worker["worker_id"],
        "name": worker["name"],
        "weather": weather,
        "predicted_income": round(predicted_income, 1),
        "shortfall": round(float(decision["shortfall"]), 1),
        "action": decision["action"],
        "loan_amount": decision["loan_amount"],
        "sweep_amount": decision["sweep_amount"],
        "reasons": reasons,
        "source": source,
    }


def _starting_ledger() -> dict[int, dict[str, Any]]:
    return {
        worker["worker_id"]: {
            "balance_inr": 1200,
            "vault_inr": 300,
            "loan_outstanding_inr": 0,
            "paid": False,
            "last_payout_tx": None,
        }
        for worker in WORKERS
    }


def _openweather() -> dict[str, Any]:
    """Return current Mumbai weather and mapped AQI, or raise for scenario fallback."""
    import os
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENWEATHER_API_KEY is not set")
    params = {"lat": 19.076, "lon": 72.877, "appid": api_key}
    current = requests.get(
        "https://api.openweathermap.org/data/2.5/weather", params=params, timeout=3
    )
    current.raise_for_status()
    pollution = requests.get(
        "https://api.openweathermap.org/data/2.5/air_pollution", params=params, timeout=3
    )
    pollution.raise_for_status()
    rain_mm = float(current.json().get("rain", {}).get("1h", 0))
    # OpenWeather's 1-5 index maps to representative values in the demo AQI range.
    aqi_scale = {1: 50, 2: 100, 3: 150, 4: 250, 5: 400}
    aqi_index = int(pollution.json()["list"][0]["main"]["aqi"])
    return {"source": "openweathermap", "rain_mm": rain_mm, "aqi": aqi_scale[aqi_index]}


@app.get("/api/health")
def health() -> dict[str, Any]:
    with STATE_LOCK:
        scenario = STATE["scenario"]
    try:
        connected = chain_connected()
    except Exception:
        logger.exception("Chain health check failed")
        connected = False
    return {
        "status": "ok",
        "scenario": scenario,
        "chain_connected": connected,
        "model_loaded": MODEL is not None and EXPLAINER is not None,
    }


@app.get("/api/workers")
def workers() -> list[dict[str, Any]]:
    with STATE_LOCK:
        paid = {
            worker_id: ledger["paid"]
            for worker_id, ledger in STATE["ledger"].items()
        }
    return [
        {
            "worker_id": worker["worker_id"],
            "name": worker["name"],
            "address": worker["address"],
            "lat": worker["lat"],
            "lng": worker["lng"],
            "paid": paid[worker["worker_id"]],
        }
        for worker in WORKERS
    ]


@app.get("/api/worker/{worker_id}")
def worker(worker_id: int) -> dict[str, Any]:
    return _worker_response(worker_id)


@app.get("/api/predict/{worker_id}")
def predict(worker_id: int) -> dict[str, Any]:
    worker_data = _worker_config(worker_id)
    with STATE_LOCK:
        scenario = STATE["scenario"]
    return _predict(worker_data, scenario)


@app.post("/api/simulate-storm")
def simulate_storm() -> dict[str, Any]:
    # Real: local-chain contract calls. Simulated: INR ledger and pool accounting.
    with ACTION_LOCK:
        with STATE_LOCK:
            STATE["scenario"] = "storm"
        new_payouts = []
        for worker_data in WORKERS:
            worker_id = worker_data["worker_id"]
            with STATE_LOCK:
                if STATE["ledger"][worker_id]["paid"]:
                    continue
            tx_hash, mock = trigger_payout(worker_data["address"])
            payout = {
                "worker_id": worker_id,
                "name": worker_data["name"],
                "address": worker_data["address"],
                "tx_hash": tx_hash,
                "amount": PAYOUT_INR,
                "mock": mock,
            }
            with STATE_LOCK:
                ledger = STATE["ledger"][worker_id]
                ledger["balance_inr"] += PAYOUT_INR
                ledger["paid"] = True
                ledger["last_payout_tx"] = tx_hash
                STATE["payout_log"].append(payout)
                new_payouts.append(payout)
        return {
            "status": "success",
            "payouts_triggered": len(new_payouts),
            "total_amount": len(new_payouts) * PAYOUT_INR,
            "payouts": new_payouts,
        }


@app.get("/api/payouts")
def payouts() -> list[dict[str, Any]]:
    with STATE_LOCK:
        return list(reversed([dict(item) for item in STATE["payout_log"]]))


@app.post("/api/loan/accept/{worker_id}")
def accept_loan(worker_id: int) -> dict[str, Any]:
    worker_data = _worker_config(worker_id)
    with ACTION_LOCK:
        with STATE_LOCK:
            scenario = STATE["scenario"]
            outstanding = STATE["ledger"][worker_id]["loan_outstanding_inr"]
        action = _predict(worker_data, scenario)
        if outstanding != 0:
            raise HTTPException(status_code=400, detail="Worker already has an outstanding loan")
        if action["action"] != "OFFER_LOAN":
            raise HTTPException(status_code=400, detail="Worker is not currently eligible for a loan")
        amount = int(action["loan_amount"])
        with STATE_LOCK:
            ledger = STATE["ledger"][worker_id]
            ledger["balance_inr"] += amount
            ledger["loan_outstanding_inr"] = amount
    return _worker_response(worker_id)


@app.post("/api/scenario/{name}")
def set_scenario(name: str) -> dict[str, str]:
    if name not in ("clear", "rainy"):
        raise HTTPException(status_code=400, detail="Scenario must be 'clear' or 'rainy'")
    with ACTION_LOCK, STATE_LOCK:
        STATE["scenario"] = name
    return {"status": "ok", "scenario": name}


@app.post("/api/reset")
def reset() -> dict[str, str]:
    with ACTION_LOCK, STATE_LOCK:
        STATE["scenario"] = "clear"
        STATE["payout_log"] = []
        STATE["ledger"] = _starting_ledger()
    return {"status": "reset"}


@app.get("/api/weather")
def weather() -> dict[str, Any]:
    try:
        return _openweather()
    except Exception:
        logger.exception("Live weather unavailable; returning scenario weather")
    with STATE_LOCK:
        scenario = STATE["scenario"]
    return {"source": "scenario", **SCENARIOS[scenario]}
