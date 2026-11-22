"""Small HTTP client for the FlowState backend."""

from __future__ import annotations

import os
from typing import Any

import requests


API_BASE_URL = os.getenv("FLOWSTATE_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT_SECONDS = 5


class ApiError(RuntimeError):
    """Backend request failed; detail contains the most useful message."""


def _request(method: str, path: str, *, payload: dict[str, Any] | None = None,
             token: str | None = None) -> Any:
    headers = {"Authorization": f"Bearer {token}"} if token else None
    try:
        response = requests.request(
            method,
            f"{API_BASE_URL}{path}",
            timeout=REQUEST_TIMEOUT_SECONDS,
            json=payload,
            headers=headers,
        )
    except requests.RequestException as exc:
        raise ApiError(f"Cannot reach backend at {API_BASE_URL}: {exc}") from exc

    if not response.ok:
        try:
            detail = response.json().get("detail")
        except (ValueError, AttributeError):
            detail = None
        raise ApiError(str(detail) if detail is not None else f"Backend returned HTTP {response.status_code}.")
    try:
        return response.json()
    except ValueError as exc:
        raise ApiError("Backend returned an invalid JSON response.") from exc


def _object_response(payload: Any, description: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ApiError(f"Backend returned an invalid {description} response.")
    return payload


def get_health() -> dict[str, Any]:
    return _object_response(_request("GET", "/api/health"), "health")


def get_workers() -> list[dict[str, Any]]:
    payload = _request("GET", "/api/workers")
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ApiError("Backend returned an invalid workers response.")
    return payload


def get_prediction(worker_id: int) -> dict[str, Any]:
    return _object_response(_request("GET", f"/api/predict/{worker_id}"), "prediction")


def set_scenario(name: str) -> dict[str, Any]:
    return _object_response(_request("POST", f"/api/scenario/{name}"), "scenario")


def simulate_storm() -> dict[str, Any]:
    return _object_response(_request("POST", "/api/simulate-storm"), "storm simulation")


def get_payouts() -> list[dict[str, Any]]:
    payload = _request("GET", "/api/payouts")
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ApiError("Backend returned an invalid payouts response.")
    return payload


def reset_demo() -> dict[str, Any]:
    return _object_response(_request("POST", "/api/reset"), "reset")


def get_worker(worker_id: int) -> dict[str, Any]:
    return _object_response(_request("GET", f"/api/worker/{worker_id}"), "worker")


def accept_loan(worker_id: int) -> dict[str, Any]:
    return _object_response(_request("POST", f"/api/loan/accept/{worker_id}"), "loan acceptance")


def get_weather() -> dict[str, Any]:
    return _object_response(_request("GET", "/api/weather"), "weather")


def auth_signup(name: str, email: str, password: str) -> dict[str, Any]:
    return _object_response(_request("POST", "/api/auth/signup", payload={
        "name": name, "email": email, "password": password,
    }), "signup")


def auth_login(email: str, password: str) -> dict[str, Any]:
    return _object_response(_request("POST", "/api/auth/login", payload={
        "email": email, "password": password,
    }), "login")


def auth_me(token: str) -> dict[str, Any]:
    return _object_response(_request("GET", "/api/auth/me", token=token), "profile")


def auth_logout(token: str) -> dict[str, Any]:
    return _object_response(_request("POST", "/api/auth/logout", token=token), "logout")
