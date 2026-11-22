"""PostgreSQL persistence for FlowState's demo state."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone, timedelta
import hashlib
import secrets
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, create_engine, delete, text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

try:
    from .config import WORKERS
except ImportError:
    from config import WORKERS


logger = logging.getLogger(__name__)
BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    raise RuntimeError("Set DATABASE_URL in backend/.env to connect to PostgreSQL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class DemoState(Base):
    __tablename__ = "demo_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario: Mapped[str] = mapped_column(String(16), nullable=False)


class WorkerLedger(Base):
    __tablename__ = "worker_ledger"

    worker_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    balance_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    vault_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    loan_outstanding_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    paid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    last_payout_tx: Mapped[str | None] = mapped_column(String(66), nullable=True)


class PayoutRecord(Base):
    __tablename__ = "payout_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    worker_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    address: Mapped[str] = mapped_column(String(42), nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(66), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    mock: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class UserAccount(Base):
    __tablename__ = "user_accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_salt: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class UserSession(Base):
    __tablename__ = "user_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


def _password_digest(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 310_000).hex()


def register_user(name: str, email: str, password: str) -> dict[str, Any] | None:
    normalized = email.strip().lower()
    salt = secrets.token_hex(16)
    with SessionLocal.begin() as session:
        if session.scalar(select(UserAccount).where(UserAccount.email == normalized)):
            return None
        user = UserAccount(name=name.strip(), email=normalized, password_salt=salt,
                           password_hash=_password_digest(password, salt))
        session.add(user)
        session.flush()
        return {"id": user.id, "name": user.name, "email": user.email}


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    with SessionLocal() as session:
        user = session.scalar(select(UserAccount).where(UserAccount.email == email.strip().lower()))
        if user is None:
            return None
        candidate = _password_digest(password, user.password_salt)
        if not secrets.compare_digest(candidate, user.password_hash):
            return None
        return {"id": user.id, "name": user.name, "email": user.email}


def create_user_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with SessionLocal.begin() as session:
        session.add(UserSession(token_hash=token_hash, user_id=user_id,
                                expires_at=datetime.now(timezone.utc) + timedelta(days=7)))
    return token


def user_for_session(token: str) -> dict[str, Any] | None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with SessionLocal() as session:
        auth_session = session.get(UserSession, token_hash)
        if auth_session is None or auth_session.revoked:
            return None
        expiry = auth_session.expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry <= datetime.now(timezone.utc):
            return None
        user = session.get(UserAccount, auth_session.user_id)
        return {"id": user.id, "name": user.name, "email": user.email} if user else None


def revoke_user_session(token: str) -> None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with SessionLocal.begin() as session:
        auth_session = session.get(UserSession, token_hash)
        if auth_session:
            auth_session.revoked = True


def initialize_database() -> None:
    """Create demo tables and seed missing state without resetting existing rows."""
    Base.metadata.create_all(engine)
    with SessionLocal.begin() as session:
        if session.get(DemoState, 1) is None:
            session.add(DemoState(id=1, scenario="clear"))
        for worker in WORKERS:
            if session.get(WorkerLedger, worker["worker_id"]) is None:
                session.add(
                    WorkerLedger(
                        worker_id=worker["worker_id"],
                        balance_inr=1200,
                        vault_inr=300,
                        loan_outstanding_inr=0,
                        paid=False,
                        last_payout_tx=None,
                    )
                )


def database_connected() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("PostgreSQL health check failed")
        return False


def get_scenario() -> str:
    with SessionLocal() as session:
        state = session.get(DemoState, 1)
        return state.scenario if state else "clear"


def set_scenario(scenario: str) -> None:
    with SessionLocal.begin() as session:
        state = session.get(DemoState, 1)
        if state is None:
            session.add(DemoState(id=1, scenario=scenario))
        else:
            state.scenario = scenario


def get_ledger(worker_id: int) -> dict[str, Any]:
    with SessionLocal() as session:
        ledger = session.get(WorkerLedger, worker_id)
        if ledger is None:
            raise KeyError(worker_id)
        return {
            "balance_inr": ledger.balance_inr,
            "vault_inr": ledger.vault_inr,
            "loan_outstanding_inr": ledger.loan_outstanding_inr,
            "paid": ledger.paid,
            "last_payout_tx": ledger.last_payout_tx,
        }


def get_paid_flags() -> dict[int, bool]:
    with SessionLocal() as session:
        return {
            ledger.worker_id: ledger.paid
            for ledger in session.query(WorkerLedger).all()
        }


def record_payout(payout: dict[str, Any]) -> None:
    """Persist payout history and its ledger credit in one database transaction."""
    with SessionLocal.begin() as session:
        ledger = session.get(WorkerLedger, payout["worker_id"])
        if ledger is None:
            raise KeyError(payout["worker_id"])
        ledger.balance_inr += payout["amount"]
        ledger.paid = True
        ledger.last_payout_tx = payout["tx_hash"]
        session.add(
            PayoutRecord(
                worker_id=payout["worker_id"],
                name=payout["name"],
                address=payout["address"],
                tx_hash=payout["tx_hash"],
                amount=payout["amount"],
                mock=payout["mock"],
            )
        )


def list_payouts() -> list[dict[str, Any]]:
    with SessionLocal() as session:
        records = (
            session.query(PayoutRecord)
            .order_by(PayoutRecord.id.desc())
            .all()
        )
        return [
            {
                "worker_id": record.worker_id,
                "name": record.name,
                "address": record.address,
                "tx_hash": record.tx_hash,
                "amount": record.amount,
                "mock": record.mock,
            }
            for record in records
        ]


def apply_loan(worker_id: int, amount: int) -> None:
    with SessionLocal.begin() as session:
        ledger = session.get(WorkerLedger, worker_id)
        if ledger is None:
            raise KeyError(worker_id)
        ledger.balance_inr += amount
        ledger.loan_outstanding_inr = amount


def reset_database() -> None:
    with SessionLocal.begin() as session:
        session.execute(delete(PayoutRecord))
        for worker in WORKERS:
            ledger = session.get(WorkerLedger, worker["worker_id"])
            if ledger is None:
                ledger = WorkerLedger(worker_id=worker["worker_id"])
                session.add(ledger)
            ledger.balance_inr = 1200
            ledger.vault_inr = 300
            ledger.loan_outstanding_inr = 0
            ledger.paid = False
            ledger.last_payout_tx = None
        state = session.get(DemoState, 1)
        if state is None:
            session.add(DemoState(id=1, scenario="clear"))
        else:
            state.scenario = "clear"
