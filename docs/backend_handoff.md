# FlowState backend handoff

For the Streamlit engineer integrating with the local FastAPI service.

## Base URL and startup order

The API base URL is `http://127.0.0.1:8000` (also reachable as `http://localhost:8000`). CORS allows all origins for the demo.

Start the services in this order, in separate PowerShell terminals. Do not use `--reload`; the backend loads its model once at startup.

### One-time backend setup

From the project root:

```powershell
cd backend
py -3.11 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` and set `RPC_URL=http://127.0.0.1:8545`, `PRIVATE_KEY` to the local Hardhat account #0 key shown in the node terminal, and `DATABASE_URL` to your local PostgreSQL connection string. Keep `.env` private and out of Git. `OPENWEATHER_API_KEY` is optional.

PostgreSQL must be installed and running locally. Create a database named `flowstate` (for example, in SQL Shell / psql):

```sql
CREATE DATABASE flowstate;
```

Set `DATABASE_URL` in `backend/.env` using the PostgreSQL username, password, host, port, and database. For the default local PostgreSQL account, the format is `postgresql+psycopg://postgres:YOUR_POSTGRES_PASSWORD@127.0.0.1:5432/flowstate`. URL-encode special characters in the password. The pinned Python dependencies are installed with the pip command above. On startup the backend creates its demo tables and seeds any missing worker rows.

Train the model once if `backend/models/model.joblib` and `explainer.joblib` are absent:

```powershell
.\venv\Scripts\python.exe train_model.py
```

### Terminal 1: local chain

```powershell
cd C:\Users\prach\OneDrive\Desktop\flowState\FlowState\contracts
npm install
npx.cmd hardhat node
```

Keep this terminal open. Hardhat node state is temporary; after restarting it, redeploy the contract in Terminal 2.

### Terminal 2: deploy and fund the contract

```powershell
cd C:\Users\prach\OneDrive\Desktop\flowState\FlowState\contracts
npx.cmd hardhat run scripts/deploy.js --network localhost
```

This writes `backend/contract/deployment.json` and funds the local payout pool with 1 ETH.

### Terminal 3: backend API

```powershell
cd C:\Users\prach\OneDrive\Desktop\flowState\FlowState\backend
.\venv\Scripts\python.exe -m uvicorn main:app --port 8000
```

Wait for `Application startup complete`. Leave this terminal running while the Streamlit apps use the API. If port 8000 is already in use, the API is probably already running; do not start a duplicate process.

## Endpoints

All response examples below are JSON. Amounts in `*_inr`, `amount`, and `loan_amount` are INR. Worker IDs are 1 to 10. Unknown IDs return HTTP 404.

### `GET /api/health`

```json
{"status":"ok","scenario":"clear","chain_connected":true,"model_loaded":true,"database_connected":true}
```

`chain_connected` reports whether the configured RPC answers. `model_loaded` reports whether both model and SHAP assets loaded. `database_connected` reports whether PostgreSQL answers.

### `GET /api/workers`

Returns all ten workers and their payout flags. Example item:

```json
[{"worker_id":1,"name":"Ravi","address":"0x70997970C51812dc3A010C7d01b50e0d17dc79C8","lat":19.076,"lng":72.878,"paid":false}]
```

### `GET /api/worker/{id}`

Returns the worker's current simulated INR ledger:

```json
{"worker_id":1,"name":"Ravi","balance_inr":1200,"vault_inr":300,"loan_outstanding_inr":0,"last_payout_tx":null}
```

### `GET /api/predict/{id}`

Returns a forecast and recommendation. This endpoint never pays or changes the ledger. Example for Ravi in clear weather:

```json
{"worker_id":1,"name":"Ravi","weather":{"scenario":"clear","rain_mm":5,"aqi":120},"predicted_income":802.9,"shortfall":0.0,"action":"NONE","loan_amount":0,"sweep_amount":0,"reasons":["Normal conditions: no income drop expected"],"source":"model"}
```

`action` is `TRIGGER_PAYOUT`, `OFFER_LOAN`, or `NONE`; `source` is `model` or `fallback`. Predictions use the selected demo scenario, not live weather.

### `POST /api/simulate-storm`

Sets the scenario to storm and processes unpaid workers sequentially. It waits for each chain receipt; if the chain call fails, that item has a mock hash and `mock: true`. Already paid workers are skipped.

```json
{"status":"success","payouts_triggered":10,"total_amount":5000,"payouts":[{"worker_id":1,"name":"Ravi","address":"0x70997970C51812dc3A010C7d01b50e0d17dc79C8","tx_hash":"0x<64 hex characters>","amount":500,"mock":false}]}
```

The displayed `payouts` array above shows one representative item; a first run returns all ten items. A repeat returns zero payouts and an empty array.

### `GET /api/payouts`

Returns payout history newest first, using the same item shape as `/api/simulate-storm`:

```json
[{"worker_id":10,"name":"Karan","address":"0xBcd4042DE499D14e55001CcbB24a551F3b954096","tx_hash":"0x<64 hex characters>","amount":500,"mock":false}]
```

### `POST /api/loan/accept/{id}`

Accepts the current `OFFER_LOAN`, adds its amount to the simulated balance, and records it as outstanding. Returns the updated worker object, for example:

```json
{"worker_id":1,"name":"Ravi","balance_inr":1222,"vault_inr":300,"loan_outstanding_inr":22,"last_payout_tx":null}
```

Returns HTTP 400 if the worker is not currently offered a loan or already has an outstanding loan.

### `POST /api/scenario/{name}`

Only `clear` and `rainy` are accepted. Changing scenario does not pay anyone.

```json
{"status":"ok","scenario":"rainy"}
```

An unsupported name returns HTTP 400.

### `POST /api/reset`

Resets scenario, ledger, paid flags, and payout history to initial demo values:

```json
{"status":"reset"}
```

### `GET /api/weather`

Informational only; it does not affect predictions. With no API key or if OpenWeather fails, it returns the selected scenario. Example:

```json
{"source":"scenario","rain_mm":5,"aqi":120}
```

When `OPENWEATHER_API_KEY` is configured and both requests succeed, source is `openweathermap`. Rain is the current 1-hour rainfall; the OpenWeather pollution index (1 to 5) is mapped to representative demo AQI values.

## Polling and demo flow

After `POST /api/simulate-storm`, poll `GET /api/worker/{id}` and `GET /api/payouts` every 2 to 3 seconds to update balances, payout status, and transaction hashes. Treat `mock: true` as a simulated proof hash, not a chain transaction. The storm endpoint itself waits for all workers before returning.

Suggested demo sequence:

1. `GET /api/health` and confirm both `chain_connected` and `model_loaded` are true.
2. Read `GET /api/predict/1` and `GET /api/workers` in clear weather.
3. Call `POST /api/simulate-storm`; show the returned payout count and transaction hashes.
4. Poll worker balances and `/api/payouts`.
5. Call `POST /api/reset` before another run.

To show the loan flow, reset, call `POST /api/scenario/rainy`, read `/api/predict/{id}` for a worker whose action is `OFFER_LOAN`, then call `POST /api/loan/accept/{id}`.

## Known limits

- The scenario, INR ledger, and payout log are stored in PostgreSQL and survive backend restarts. `/api/reset` clears payout history and restores the initial demo values.
- For this MVP, SQLAlchemy creates tables at startup; there is no Alembic migration history yet. Back up the database before changing table definitions.
- The local Hardhat chain is ephemeral. Restarting its node requires redeploying the contract and restarting the backend if it is already serving requests.
- If the chain, contract, signing key, or RPC is unavailable, payout calls return mock hashes and still update the simulated INR ledger. Check `mock` on each payout.
- Worker earnings, weather scenarios, balances, vaults, funding pool accounting, and loan repayment are demo simulations. There is no real bank/UPI transfer, KYC, or loan repayment flow.
- Synthetic model artifacts are local files and are ignored by Git. A fresh clone needs `train_model.py`; if assets are unavailable, predictions use the formula fallback.
- The optional weather endpoint maps OpenWeather's pollution category to representative AQI values. Decision logic always uses hardcoded scenario values.
