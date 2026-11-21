"""Shared constants and fixed demo data for the FlowState backend."""

SURVIVAL_THRESHOLD_INR = 500
RAIN_THRESHOLD_MM = 50
AQI_THRESHOLD = 400
PAYOUT_INR = 500
PAYOUT_ETH = 0.0005
DISPLAY_INR_PER_ETH = 1_000_000
REPAYMENT_SHARE = 0.15
DEMO_DAY_OF_WEEK = 2  # Monday=0; Wednesday keeps demo predictions deterministic.

SCENARIOS = {
    "clear": {"rain_mm": 5, "aqi": 120},
    "storm": {"rain_mm": 80, "aqi": 450},
    "rainy": {"rain_mm": 45, "aqi": 250},
}

# The ledger, weather, earnings, pool funding, and loan repayment are simulated.
# Prediction, decision rules, SHAP, and local-chain contract execution are real.
WORKERS = [
    {
        "worker_id": 1,
        "name": "Ravi",
        "baseline": 850,
        "address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "lat": 19.076,
        "lng": 72.878,
    },
    {
        "worker_id": 2,
        "name": "Amit",
        "baseline": 780,
        "address": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
        "lat": 19.086,
        "lng": 72.888,
    },
    {
        "worker_id": 3,
        "name": "Suresh",
        "baseline": 900,
        "address": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
        "lat": 19.066,
        "lng": 72.868,
    },
    {
        "worker_id": 4,
        "name": "Imran",
        "baseline": 700,
        "address": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
        "lat": 19.076,
        "lng": 72.858,
    },
    {
        "worker_id": 5,
        "name": "Deepak",
        "baseline": 950,
        "address": "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",
        "lat": 19.056,
        "lng": 72.878,
    },
    {
        "worker_id": 6,
        "name": "Manoj",
        "baseline": 820,
        "address": "0x976EA74026E726554dB657fA54763abd0C3a0aa9",
        "lat": 19.096,
        "lng": 72.868,
    },
    {
        "worker_id": 7,
        "name": "Sanjay",
        "baseline": 760,
        "address": "0x14dC79964da2C08b23698B3D3cc7Ca32193d9955",
        "lat": 19.056,
        "lng": 72.898,
    },
    {
        "worker_id": 8,
        "name": "Vikram",
        "baseline": 880,
        "address": "0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f",
        "lat": 19.096,
        "lng": 72.898,
    },
    {
        "worker_id": 9,
        "name": "Arjun",
        "baseline": 640,
        "address": "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720",
        "lat": 19.036,
        "lng": 72.878,
    },
    {
        "worker_id": 10,
        "name": "Karan",
        "baseline": 990,
        "address": "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
        "lat": 19.116,
        "lng": 72.878,
    },
]
