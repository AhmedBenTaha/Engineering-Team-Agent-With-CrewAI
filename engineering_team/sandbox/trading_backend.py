"""Simple account management system for a trading simulation platform."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Literal, Tuple, Optional
from dataclasses import dataclass, field


# ----------------------------------------------------------------------
# Helper: share price lookup (test stub returns fixed prices)
def get_share_price(symbol: str) -> float:
    """Return current price for a symbol. Test implementation returns fixed values."""
    _prices: Dict[str, float] = {
        "AAPL": 150.0,
        "TSLA": 250.0,
        "GOOGL": 2800.0,
    }
    if symbol not in _prices:
        raise ValueError(f"Unknown symbol '{symbol}'")
    return _prices[symbol]


# ----------------------------------------------------------------------
# Data models

@dataclass
class Transaction:
    id: str
    type: Literal["deposit", "withdraw", "buy", "sell"]
    symbol: str | None
    quantity: float | None
    price: float | None
    amount: float          # cash moved (positive for deposit/buy, negative for withdraw/sell)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Holding:
    symbol: str
    quantity: float


@dataclass
class UserAccount:
    user_id: str
    balance: float = 0.0
    initial_deposit: float = 0.0
    transactions: List[Transaction] = field(default_factory=list)
    holdings: Dict[str, Holding] = field(default_factory=dict)


# ----------------------------------------------------------------------
# In‑memory store
_user_store: Dict[str, UserAccount] = {}


# ----------------------------------------------------------------------
# Account Management

def create_account(user_id: str) -> UserAccount:
    """Create a new account with zero balance. Raises ValueError if user already exists."""
    if user_id in _user_store:
        raise ValueError(f"User '{user_id}' already exists.")
    account = UserAccount(user_id=user_id)
    _user_store[user_id] = account
    return account


def deposit_funds(user_id: str, amount: float) -> float:
    """Add cash to balance; sets initial_deposit on first deposit. Returns new balance."""
    if amount <= 0:
        raise ValueError("Deposit amount must be positive.")
    account = _ensure_user(user_id)
    account.balance += amount
    if account.initial_deposit == 0.0:
        account.initial_deposit = amount
    _record_transaction(account, Transaction(
        id=uuid.uuid4().hex,
        type="deposit",
        symbol=None,
        quantity=None,
        price=None,
        amount=amount,
    ))
    return account.balance


def withdraw_funds(user_id: str, amount: float) -> float:
    """Subtract cash if sufficient balance. Raises ValueError on insufficient funds. Returns new balance."""
    if amount <= 0:
        raise ValueError("Withdrawal amount must be positive.")
    account = _ensure_user(user_id)
    if amount > account.balance:
        raise ValueError("Insufficient funds for withdrawal.")
    account.balance -= amount
    _record_transaction(account, Transaction(
        id=uuid.uuid4().hex,
        type="withdraw",
        symbol=None,
        quantity=None,
        price=None,
        amount=-amount,  # negative cash moved
    ))
    return account.balance


# ----------------------------------------------------------------------
# Trading Operations

def buy_shares(user_id: str, symbol: str, quantity: float) -> Tuple[float, float]:
    """
    Purchase `quantity` shares of `symbol` at current price.
    Returns (total_cost, new_balance). Raises ValueError on insufficient cash or invalid inputs.
    """
    if quantity <= 0:
        raise ValueError("Quantity must be positive.")
    price = get_share_price(symbol)
    total_cost = quantity * price
    account = _ensure_user(user_id)
    if account.balance < total_cost:
        raise ValueError("Insufficient cash to buy shares.")
    account.balance -= total_cost
    # Update holdings
    if symbol in account.holdings:
        account.holdings[symbol].quantity += quantity
    else:
        account.holdings[symbol] = Holding(symbol=symbol, quantity=quantity)
    _record_transaction(account, Transaction(
        id=uuid.uuid4().hex,
        type="buy",
        symbol=symbol,
        quantity=quantity,
        price=price,
        amount=total_cost,  # positive cash moved out
    ))
    return total_cost, account.balance


def sell_shares(user_id: str, symbol: str, quantity: float) -> Tuple[float, float]:
    """
    Sell `quantity` shares of `symbol` at current price.
    Returns (proceeds, new_balance). Raises ValueError on insufficient holdings or invalid inputs.
    """
    if quantity <= 0:
        raise ValueError("Quantity must be positive.")
    price = get_share_price(symbol)
    account = _ensure_user(user_id)
    holding = account.holdings.get(symbol)
    if holding is None or holding.quantity < quantity:
        raise ValueError(f"Insufficient holdings of {symbol} to sell.")
    proceeds = quantity * price
    account.balance += proceeds
    holding.quantity -= quantity
    if holding.quantity == 0:
        del account.holdings[symbol]
    _record_transaction(account, Transaction(
        id=uuid.uuid4().hex,
        type="sell",
        symbol=symbol,
        quantity=quantity,
        price=price,
        amount=-proceeds,  # negative cash moved
    ))
    return proceeds, account.balance


# ----------------------------------------------------------------------
# Portfolio Reporting

def get_holdings(user_id: str) -> List[Holding]:
    """Return a snapshot list of current holdings (symbol + quantity)."""
    account = _ensure_user(user_id)
    return list(account.holdings.values())


def get_portfolio_value(user_id: str) -> float:
    """Sum of cash balance + market value of all holdings (using `get_share_price`)."""
    account = _ensure_user(user_id)
    market_value = sum(
        h.quantity * get_share_price(h.symbol) for h in account.holdings.values()
    )
    return account.balance + market_value


def get_profit_loss(user_id: str) -> float:
    """Return current portfolio value minus the initial deposit."""
    account = _ensure_user(user_id)
    return get_portfolio_value(user_id) - account.initial_deposit


def list_transactions(user_id: str) -> List[Transaction]:
    """Chronological list of all transactions for the user."""
    account = _ensure_user(user_id)
    return sorted(account.transactions, key=lambda tx: tx.timestamp)


# ----------------------------------------------------------------------
# Internal helpers (private)

def _ensure_user(user_id: str) -> UserAccount:
    """Retrieve account or raise KeyError if not found."""
    if user_id not in _user_store:
        raise KeyError(f"User '{user_id}' not found.")
    return _user_store[user_id]


def _record_transaction(account: UserAccount, tx: Transaction) -> None:
    """Append transaction and keep list sorted by timestamp."""
    account.transactions.append(tx)
    # sort by timestamp ascending
    account.transactions.sort(key=lambda t: t.timestamp)
