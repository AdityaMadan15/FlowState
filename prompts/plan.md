# FlowState: Complete Project Plan

> **One-liner:** Loan apps react after a worker is broke. FlowState acts the day before.

**Event:** 18-hour fintech hackathon (80 teams) | **Team:** 4 people | **Goal:** a flawless end-to-end demo and a confident pitch

---

## 1. The Project in Plain Words

FlowState predicts when a gig worker is about to lose income (heavy rain, bad pollution) and **automatically gives them money before the bad day hits**.

**Predict, then pay.**

- **Predict:** an AI forecasts tomorrow's income from weather and past earnings.
- **Pay:** money reaches the worker one of two ways:
  - a **free payout** when severe weather actually crosses a threshold (insurance-style, never repaid)
  - a **small loan** when the AI predicts a shortfall without a severe event (repaid from future earnings)

---

## 2. The Problem

India has millions of gig workers (Swiggy/Zomato riders, Uber drivers, Urban Company technicians). They are paid per task, so no orders means no money.

**Meet Ravi,** a Zomato rider in Mumbai:

- Good day: about ₹800
- Heavy-rain day: about ₹0
- Rent, EMI and groceries **do not stop**

**Why he is stuck:**

1. **Banks say no.** No salary slip, so he is "thin-file".
2. **Loan apps say yes,** but at 40%+ APR. One bad week turns into months of debt.
3. **Insurance is slow.** Forms, proof, weeks of waiting.

Every existing option helps **after** the worker is broke. Nobody helps **before**.

---

## 3. The Solution: Four Features

| Feature | What it does | Priority |
|---|---|---|
| **AI Predictor** | Forecasts tomorrow's income and explains why (SHAP) | P0 |
| **Parametric Payout** | Free ₹500 via smart contract when weather crosses a threshold | P0 |
| **Flex-Loan** | Small advance covering the gap when a shortfall is predicted | P1 |
| **Auto-Sweep** | Saves ~10% of income on big days into a vault | P2 |

---

## 4. Decision Rules (Single Source of Truth)

**Constants**

```
SURVIVAL_THRESHOLD_INR = 500
RAIN_THRESHOLD_MM      = 50
AQI_THRESHOLD          = 400
PAYOUT_INR             = 500   (on-chain: 0.0005 ETH, display rate 1 ETH = ₹1,000,000)
REPAYMENT_SHARE        = 15%   (of future daily earnings, capped)
```

**Evaluated per worker, in this order**

| # | Condition | Action | Money type |
|---|---|---|---|
| 1 | `rain_mm > 50` OR `aqi > 400` | `TRIGGER_PAYOUT` | Free, paid by funding pool via smart contract |
| 2 | else if `predicted_income < 500` | `OFFER_LOAN` (amount = 500 − predicted) | Repayable |
| 3 | else | `NONE` | none |
| Stretch | `predicted_income > 1000` | `sweep_amount` = 10% to vault | Savings |

**Key distinction:** a payout is a **fact** (the weather crossed a line). A loan is a **prediction** (the AI expects a shortfall).

**Worked examples**

- **Storm (80mm, AQI 450):** 80 > 50, so a ₹500 payout fires.
- **Moderate day (30mm), predicted ₹320:** no payout, but 320 < 500, so a ₹180 loan is offered.
- **Clear day, predicted ₹850:** nothing happens.

---

## 5. How Everything Moves (Data Flow)

```
 Weather (mock scenario: clear / storm)
        |
        v
 LightGBM predicts tomorrow's income
        |
        v
 SHAP explains the top reasons
        |
        v
 Decision rules (payout / loan / none)
        |
        v
 FastAPI backend
        |
        v
 web3.py sends a transaction
        |
        v
 Solidity contract on Hardhat releases funds
        |
        v
 Streamlit Worker App + Admin Dashboard update
```

**In one sentence:** data comes in, the AI predicts, the rules decide, the smart contract pays, the app shows.

| Piece | Role |
|---|---|
| Weather source | The project's eyes |
| LightGBM + SHAP | The brain and its explanation |
| FastAPI | The messenger connecting everything |
| web3.py | The backend's hand on the blockchain |
| Smart contract | Vault with fixed, automatic rules (the trust layer) |
| Worker app | Ravi's wallet and alerts |
| Admin dashboard | The control room with the map and the red button |

---

## 6. Tech Stack (100% Free)

| Layer | Tool | Why |
|---|---|---|
| AI | LightGBM, pandas, scikit-learn | Fast to train, accurate on small data |
| Explainability | SHAP (TreeExplainer) | Shows *why* the model predicted a drop |
| Smart contracts | Solidity + OpenZeppelin v5 on Hardhat | Free local chain, instant transactions |
| Backend | FastAPI + web3.py 6.20.0 | Python end to end, auto docs |
| Weather | Mock OpenWeatherMap with hardcoded fallback | Demo never depends on the internet |
| Worker app | Streamlit (400px mobile look) | Fastest polished UI in Python |
| Admin app | Streamlit + streamlit-folium (Leaflet) | Live map with minimal code |

**Version traps to remember**

- OpenZeppelin v5 requires `Ownable(msg.sender)` in the constructor.
- web3.py v6 uses `rawTransaction` (v7 renamed it).
- Hardhat accounts hold 10,000 ETH, so show a **₹ ledger** in the UI and use the chain for proof (tx hash).

---

## 7. Folder Structure

```
flowstate/
├── contracts/                      # Hardhat project
│   ├── contracts/FlowStatePayout.sol
│   ├── scripts/deploy.js           # writes backend/contract/deployment.json
│   └── test/payout.js
├── backend/
│   ├── main.py                     # FastAPI app and endpoints
│   ├── blockchain.py               # web3.py payout function (with mock fallback)
│   ├── train_model.py              # synthetic data + LightGBM + SHAP
│   ├── config.py                   # constants, workers, scenarios
│   ├── requirements.txt
│   ├── .env.example                # RPC_URL, PRIVATE_KEY, WEATHER_URL
│   ├── models/                     # model.joblib, explainer.joblib
│   └── contract/deployment.json    # {"address": "...", "abi": [...]}
└── frontend/
    ├── worker_app.py
    ├── admin_app.py
    ├── api_client.py               # API calls with offline mock fallback
    └── requirements.txt
```

**Ports:** Hardhat `8545` | FastAPI `8000` | Worker app `8501` | Admin app `8502`

---

## 8. Fixed Demo Data (Everyone Uses This)

- **10 workers**, ids 1 to 10.
- Worker addresses are **Hardhat accounts #1 to #10**.
- The backend signer is **account #0**, the contract owner.
- **Names:** 1 Ravi, 2 Amit, 3 Suresh, 4 Imran, 5 Deepak, 6 Manoj, 7 Sanjay, 8 Vikram, 9 Arjun, 10 Karan.
- **Location:** Mumbai, about lat 19.076, lng 72.877, with small fixed offsets (±0.05).
- **Weather scenarios**
  - `clear` = rain 5mm, AQI 120 (default)
  - `storm` = rain 80mm, AQI 450
- **Starting ledger per worker:** balance ₹1,200 | vault ₹300 | loan outstanding ₹0

---

## 9. API Contract

Base URL `http://localhost:8000`, CORS allows all origins. The backend implements this **exactly** and the frontend consumes it **exactly**.

| Method | Endpoint | Returns |
|---|---|---|
| GET | `/api/health` | `{"status":"ok","scenario":"clear","chain_connected":true}` |
| GET | `/api/workers` | list of `{worker_id, name, address, lat, lng, paid}` |
| GET | `/api/worker/{id}` | `{worker_id, name, balance_inr, vault_inr, loan_outstanding_inr, last_payout_tx}` |
| GET | `/api/predict/{id}` | prediction JSON (below) |
| POST | `/api/simulate-storm` | payout summary (below) |
| GET | `/api/payouts` | payout list, newest first |
| POST | `/api/loan/accept/{id}` (P1) | updated worker JSON |
| POST | `/api/reset` | `{"status":"reset"}` |

**`/api/predict/{id}` response**

```json
{
  "worker_id": 1, "name": "Ravi",
  "weather": {"scenario": "storm", "rain_mm": 80, "aqi": 450},
  "predicted_income": 142.5, "shortfall": 357.5,
  "action": "TRIGGER_PAYOUT",
  "loan_amount": 0, "sweep_amount": 0,
  "reasons": ["Heavy rain (80mm): -₹312", "Severe AQI (450): -₹140"]
}
```

**`/api/simulate-storm` response**

```json
{
  "status": "success", "payouts_triggered": 10, "total_amount": 5000,
  "payouts": [
    {"worker_id": 1, "name": "Ravi", "address": "0x...", "tx_hash": "0x...", "amount": 500, "mock": false}
  ]
}
```

---

## 10. Component Details

### 10.1 Smart Contract (`FlowStatePayout.sol`)

- Solidity ^0.8.20, OpenZeppelin `Ownable` and `ReentrancyGuard`.
- `PAYOUT_AMOUNT = 0.0005 ether` (simulates ₹500).
- `fundPool()` is payable, so anyone can top up the pool.
- `triggerPayout(address payable _worker)` is `onlyOwner`, requires enough balance, transfers the amount, emits `PayoutTriggered`.
- `poolBalance()` is a view function.
- No daily limit, so the demo is re-runnable (production would add one).
- `deploy.js` deploys, funds with 1 ETH, and writes `deployment.json`.
- `test/payout.js` covers three cases: owner can pay, non-owner is rejected, an empty pool reverts.

### 10.2 AI Model (`train_model.py`)

- Synthetic data: 10 workers × ~120 days. Columns: `worker_id, day_of_week, historical_daily_earnings (600-1000), rain_mm (0-100), aqi (50-500), actual_income`.
- Formula so the model learns a real pattern:
  `income = baseline × (1 − 0.0085×rain) × (1 − 0.0008×max(aqi−150, 0)) × weekend_boost(1.15) + noise(sd 30)`, floored at 0.
- About 20% of rows are heavy-rain or high-AQI.
- `LGBMRegressor(n_estimators=200, learning_rate=0.05, min_child_samples=5)`.
- SHAP `TreeExplainer` saved with joblib.
- **Self-check at the end:** the storm prediction must be below ₹500 for every worker, and the clear prediction above ₹500 for most.

### 10.3 Backend (`main.py`, `blockchain.py`)

- Loads the model and explainer once at startup. Plain `def` for ML inference (no async).
- Global state: current scenario, per-worker ledger, payout log, paid set.
- Weather function tries the mock URL and, on any failure, falls back to the scenario's hardcoded values.
- `/predict` builds a one-row DataFrame, predicts, runs SHAP, formats the top two negative contributors as friendly reasons, then applies the decision rules.
- `/simulate-storm` sets the scenario to storm, loops the 10 workers, calls `trigger_payout`, updates the ledger, and logs the result.
- `trigger_payout` builds, signs, sends and **waits for each receipt** (so nonces never collide). On any failure it returns a fake tx hash with `mock: true`.
- Handlers never return a 500, only a sensible JSON.

### 10.4 Worker App (`worker_app.py`, port 8501)

- Centered 400px column, gradient header, rounded cards (custom CSS).
- Worker selector (default Ravi).
- Cards: wallet balance, savings vault, loan outstanding.
- Forecast card: predicted income, weather chips, SHAP reasons in an alert box.
- Action states:
  - `TRIGGER_PAYOUT`: green banner and toast "₹500 Safety Payout credited instantly!" plus the short tx hash.
  - `OFFER_LOAN`: offer card with an Accept button.
  - `NONE`: calm "All good" card.
- Auto-refresh every 3 seconds so it reacts live to the admin's button.
- Plotly bar: predicted income vs the ₹500 line.

### 10.5 Admin Dashboard (`admin_app.py`, port 8502)

- Wide layout, header "FlowState HQ - Risk Command Center".
- Metrics: Active Workers, Storm Status, Funds Disbursed Today.
- Folium map of Mumbai with 10 markers (green = not paid, red = paid).
- Giant red button **🚨 SIMULATE 80mm RAINFALL**: spinner, POST, markers turn red, live payout feed, metrics update.
- Grey **Reset demo** button.
- State kept in `st.session_state`.

### 10.6 Resilience Rules

- Blockchain fails, so a mock tx hash is returned and the demo continues.
- Weather API fails, so the scenario's hardcoded values are used.
- Backend is down, so the frontend shows built-in mock data and still renders.

---

## 11. Team Roles

| Role | Owns | Output |
|---|---|---|
| **1. Backend + AI** | `train_model.py`, `main.py`, `blockchain.py`, `config.py` | Working API + model |
| **2. Blockchain** | Contract, deploy script, tests | `deployment.json`, account #0 key |
| **3. Frontend** | Worker app, admin app, `api_client.py` | Two polished Streamlit apps |
| **4. Pitcher / PM / QA** | Deck, demo script, integration testing, mock-data review | Deck, tested demo, backup video |

---

## 12. 18-Hour Timeline

| Hours | Backend + AI | Blockchain | Frontend | Pitcher / QA |
|---|---|---|---|---|
| **0-1** | Repo setup, `config.py`, agree on API contract | Hardhat setup | Streamlit skeletons | Fix deck (£ → ₹), write demo script |
| **1-4** | `train_model.py`, model + SHAP working | Contract + tests | Worker app on mock data | Review synthetic data, draft pitch |
| **4-6** | FastAPI skeleton, `/predict` | Deploy script, **hand off `deployment.json`** | Admin app + map on mock data | Prepare judge Q&A |
| **6-10** | `blockchain.py`, `/simulate-storm`, `/reset`, `/payouts` | Support integration, verify txs | Connect to real API | Test each piece as it lands |
| **10-13** | Loan endpoints (P1), error handling | Help debug chain issues | Live feed, auto-refresh, polish | **Big Merge test** |
| **13-15** | Bug fixes only | Bug fixes only | UI polish, animations | Run full checklist 3 times |
| **15** | **CODE FREEZE** | | | |
| **15-17** | Sweep (P2) only if everything is stable | Standby | Final polish | Rehearse pitch, record backup video |
| **17-18** | Standby | Standby | Standby | Final run-through, submission |

### Hard Handoffs

| Hour | Handoff | From → To |
|---|---|---|
| 4-6 | `deployment.json` and the account #0 key | Blockchain → Backend |
| 6 | Working `/predict` URL | Backend → Frontend |
| 10 | Real API replaces mock data in the apps | Frontend |
| **13** | **Big Merge:** the button triggers the API, which triggers the contract, which updates the app, end to end | Everyone |
| 15 | Code freeze | Everyone |

---

## 13. How to Run Everything (5 Terminals)

```bash
# 1. Local blockchain (keep running)
cd contracts && npm install && npx hardhat node

# 2. Deploy the contract (writes deployment.json)
cd contracts && npx hardhat run scripts/deploy.js --network localhost

# 3. Backend (first time: python train_model.py)
cd backend && uvicorn main:app --port 8000

# 4. Worker app
cd frontend && streamlit run worker_app.py --server.port 8501

# 5. Admin app
cd frontend && streamlit run admin_app.py --server.port 8502
```

Copy the account #0 private key from the `hardhat node` output into `backend/.env`.

---

## 14. The Demo (5 Minutes)

**Setup:** worker app (8501) and admin app (8502) side by side. Press Reset first.

| Step | You do | The screen shows |
|---|---|---|
| 1 | Tell Ravi's story | Worker app: "All good", forecast above ₹500 |
| 2 | Click **🚨 SIMULATE 80mm RAINFALL** | Spinner "Triggering smart contracts..." |
| 3 | **Stay silent for 3 seconds** | Map turns red, the payout feed fills |
| 4 | Point to the metric | Funds Disbursed: ₹5,000 |
| 5 | Switch to Ravi's phone | "₹500 Safety Payout credited" and the reason "Heavy rain: -₹312" |
| 6 | Close | "Loan apps react after a worker is broke. FlowState acts the day before." |

**Say while it runs:**
> "A storm has just hit. Nobody filed a claim. Nobody called anyone. The system saw it, predicted the damage, and paid out."

**Be honest:** earnings, weather and money are simulated. The real part is the logic: predict, trigger, pay.

---

## 15. QA Checklist (Run 3 Times in a Row)

- [ ] Reset: map green, worker app says "All good", Ravi's prediction above ₹500
- [ ] Both apps open side by side
- [ ] Click the red button: map turns red, 10 payouts in the feed, ₹5,000 disbursed
- [ ] Worker app shows the ₹500 notification and SHAP reasons within ~3 seconds
- [ ] Reset works and the whole flow repeats
- [ ] With the backend OFF, both apps still render with mock data
- [ ] Backup screen recording saved on the laptop

---

## 16. Risks and Fallbacks

| Risk | Fallback |
|---|---|
| Blockchain call fails | Backend returns a mock tx hash, demo continues |
| Weather API fails | Hardcoded scenario values |
| Backend crashes | Frontend shows mock data |
| Wi-Fi fails | Everything runs on localhost, no internet needed |
| Live demo crashes | Play the backup recording: "Here is the same flow recorded earlier." |
| Time runs short | Cut P2 (sweep) first, then P1 (loan), and show them as "Next phase" slides |
| Integration slips past hour 13 | Freeze features and spend the remaining time on making the P0 flow flawless |

---

## 17. Real vs Simulated (Say This Openly)

| Real | Simulated |
|---|---|
| Prediction pipeline (LightGBM) | Earnings data |
| SHAP explanations | Weather input |
| Decision rules | UPI, bank, KYC |
| Smart contract execution (local chain) | The funding pool |
| | Loan repayment |

Saying "this part is simulated" sounds confident, not weak.

---

## 18. Business Model

- **Who pays:** gig platforms (Zomato, Swiggy), insurers, and NBFCs fund the pool.
- **Why they pay:** riders stay active, fewer riders are lost (lower hiring cost), and lenders earn on safe small loans.
- **The math:** about 5 payouts × ₹500 = ₹2,500 per worker per year, roughly **₹7 a day**. That is small next to the cost of losing a rider.
- **Payout vs loan:** the payout is never repaid and is borne by the pool. The loan is repaid from future earnings.

---

## 19. Hard Questions and Answers

**Can workers lie about income?**
> Income isn't self-reported. We read it from platform data and UPI inflows, repay at the source, and flag anomalies against the AI's own forecast. Loans are tiny, so the worst-case loss per person is small.

**How is repayment protected if the worker earns nothing?**
> Repayment is a small capped share (about 15%) of actual earnings. Earn ₹0 and ₹0 is taken, with no penalties. The pool absorbs a small default rate, as in any lending.

**What if someone fakes their location for a payout?**
> We verify against platform delivery logs and device GPS, so only workers active in the storm zone qualify.

**Why blockchain and not a database?**
> The rules must be trustworthy. Thresholds and the pool are visible and cannot be quietly changed, and payouts settle automatically and are auditable.

**Isn't the AI trained on fake data?**
> Yes, this is a proof of concept. The pipeline is real. In a pilot we would train on actual platform earnings and measure forecast accuracy first.

**Who is licensed to lend or insure?**
> We partner with a licensed NBFC or insurer. FlowState is the intelligence and automation layer on top.

**How do you set the thresholds?**
> From historical data: we find the rainfall level where rider earnings collapse. 50mm is our starting value, tuned per city.

---

## 20. Rollout Plan (for the Deck)

| Phase | Timing | Goal | Metrics |
|---|---|---|---|
| **Now** | Hackathon MVP | Working prototype | End-to-end demo |
| **Next** | 3-month pilot (e.g. Bangalore) | Real platform data, licensed NBFC/insurer partner | Forecast accuracy, repayment rate |
| **Then** | 1 year | Scale across Indian cities | Workers covered, 40% APR loans avoided |

---

## 21. Pitch Delivery Cheat Sheet

1. **Open with Ravi,** not with tech.
2. **Use the one-liner twice,** at the start and at the close.
3. **Say "predict, then pay."**
4. **Stay silent for 3 seconds** after the button click.
5. **Say "our AI" and "our smart contract"** unless asked for names.
6. **Admit limits openly.**

**60-second version**

> Gig workers like Ravi earn ₹800 on a good day and ₹0 when it rains, but rent never stops. Banks reject him, and loan apps charge 40% interest. Every option helps after he's broke. FlowState acts the day before. Our AI predicts tomorrow's income from weather and his history. If severe weather hits, a smart contract automatically pays him ₹500, no forms, no claims. If it's a smaller shortfall, he gets a small advance repaid from future earnings. On good days we save a little for him. Loan apps react after a worker is broke. FlowState acts the day before.

---

## 22. Deck Fixes Before Submission

- [ ] Change every **£ to ₹** (slides 2, 3, 4, 5, 6)
- [ ] Slide 6: list **Streamlit** (not React) if that is what you build, and mention Leaflet
- [ ] Slide 4: mention **SHAP** in the core logic box
- [ ] Slide 7: add timeline labels (Now / 3 months / 1 year)
- [ ] Add an anti-fraud line (platform logs + GPS verification)
- [ ] Present the loan and sweep as "next phase" if they are not built

---

## 23. Definition of Done

**Must have (P0):** model and `/predict`, contract and payout, `/simulate-storm`, admin map with red button, worker payout notification, `/reset`.

**Should have (P1):** loan offer and accept.

**Nice to have (P2):** auto-sweep, fraud-check explanation.

> **A flawless 5-minute demo beats extra features. Always.**
