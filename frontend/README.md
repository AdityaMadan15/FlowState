# FlowState frontend

FlowState is a Streamlit dashboard for weather-linked income protection. The UI reads worker, forecast, ledger, scenario, weather, and payout values from the FastAPI backend; it does not create mock business data.

## Run the frontend

From the repository root in Windows PowerShell:

```powershell
cd frontend
py -3.11 -m venv .runvenv
.\.runvenv\Scripts\python.exe -m pip install -r requirements.txt
$env:FLOWSTATE_API_BASE_URL = "http://127.0.0.1:8000"
.\.runvenv\Scripts\python.exe -m streamlit run app.py
```

The default API URL is `http://127.0.0.1:8000`. Copy `.env.example` only as a reference; it contains no credentials. For a different API host, set `FLOWSTATE_API_BASE_URL` in the shell before starting Streamlit.

## Run the backend

PostgreSQL must be running, and a database named `flowstate` must exist. Configure `backend/.env` with a PostgreSQL `DATABASE_URL`, then install and start the API in a separate PowerShell window:

```powershell
cd backend
py -3.11 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
.\venv\Scripts\python.exe -m uvicorn main:app --port 8000
```

Set `DATABASE_URL` in `backend/.env` to the local database connection string. Keep this file private and out of Git. `OPENWEATHER_API_KEY` is optional; without it, the backend reports the selected scenario's weather. Model files are also optional because the backend has a formula fallback. Hardhat is optional; without a connected chain, the backend can return mock payout records.

## Dashboard features

- System health and live impact summary.
- Clear and rainy scenario controls.
- Per-worker predictions with individual retry, reasons, and source.
- Confirmed storm simulation and reset actions, with returned payout records.
- Payout history in backend order, without invented dates or totals.
- Worker ledger/detail, confirmed loan acceptance, and paid/unpaid worker map.
- Worker view, informational demo guide, and optional 3-second live snapshot refresh.

The auto-refresh toggle is off by default. When enabled, it refreshes backend health, weather,
the worker roster and predictions, and payout history every three seconds. The worker view is
informational and displays only values returned by the backend.

## Known API limits

- Payout history has no timestamps and the API has no historical payout-sum endpoint.
- Weather returns rain and AQI but no temperature or textual description.
- Worker coordinates are available from `/api/workers`, not `/api/worker/{worker_id}`.
- The dashboard displays these fields only when the backend supplies them; it does not infer missing history or weather details.
