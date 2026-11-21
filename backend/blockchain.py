"""Local-chain payout bridge with a safe mock fallback for demo resilience."""

from __future__ import annotations

import json
import logging
import os
import secrets
import threading
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from web3 import Web3
from web3.providers.rpc import HTTPProvider


logger = logging.getLogger(__name__)
BACKEND_DIR = Path(__file__).resolve().parent
DEPLOYMENT_PATH = BACKEND_DIR / "contract" / "deployment.json"
ENV_PATH = BACKEND_DIR / ".env"
_TX_LOCK = threading.Lock()

load_dotenv(ENV_PATH)


def _rpc_url() -> str:
    return (os.getenv("RPC_URL") or "http://127.0.0.1:8545").strip()


def _web3() -> Web3:
    return Web3(HTTPProvider(_rpc_url(), request_kwargs={"timeout": 3}))


def chain_connected() -> bool:
    """Return whether the configured JSON-RPC endpoint responds."""
    try:
        return _web3().is_connected()
    except Exception:
        logger.exception("Could not check local chain connection")
        return False


def _load_contract(w3: Web3) -> Any:
    with DEPLOYMENT_PATH.open("r", encoding="utf-8") as deployment_file:
        deployment = json.load(deployment_file)
    return w3.eth.contract(
        address=Web3.to_checksum_address(deployment["address"]),
        abi=deployment["abi"],
    )


def trigger_payout(worker_address: str) -> tuple[str, bool]:
    """Pay a worker on-chain, or return a random mock tx hash on any failure."""
    try:
        private_key = os.getenv("PRIVATE_KEY", "").strip()
        if not private_key:
            raise RuntimeError("PRIVATE_KEY is missing from backend/.env")

        with _TX_LOCK:
            w3 = _web3()
            if not w3.is_connected():
                raise ConnectionError(f"Cannot connect to local chain at {_rpc_url()}")

            account = w3.eth.account.from_key(private_key)
            contract = _load_contract(w3)
            tx = contract.functions.triggerPayout(
                Web3.to_checksum_address(worker_address)
            ).build_transaction(
                {
                    "from": account.address,
                    "nonce": w3.eth.get_transaction_count(account.address, "pending"),
                    "chainId": w3.eth.chain_id,
                    "gas": 200_000,
                    "gasPrice": w3.eth.gas_price,
                }
            )
            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
            if receipt["status"] != 1:
                raise RuntimeError(f"Payout transaction reverted: {tx_hash.hex()}")
            return tx_hash.hex(), False
    except Exception:
        logger.exception("On-chain payout failed; returning a mock transaction hash")
        return f"0x{secrets.token_hex(32)}", True
