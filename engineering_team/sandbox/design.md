# Design Document – Simple Account Management System for a Trading Simulation Platform  

**Target Audience:**  
- **backend_engineer** – Implements the core Python backend logic.  
- **frontend_engineer** – Builds a Gradio 6 UI that calls the backend functions.  
- **test_engineer** – Writes unit tests for the backend module.  

All files live in the root of the sandbox directory (no sub‑folders).  
The project is a **uv**‑managed Python environment with **gradio** (v6.x) installed.  

---  

## 1. High‑Level Architecture  

```
+-------------------+          +-------------------+          +-------------------+
|   Gradio UI (app) | <--RPC--> |   Backend Module  | <--DB--> |   In‑Memory Data   |
+-------------------+          +-------------------+          +-------------------+
```

* The **frontend** (Gradio) invokes pure‑Python functions exposed by the **backend**.  
* The **backend** maintains an in‑memory store (`dict`) keyed by `user_id`.  
* A helper function `get_share_price(symbol: str) -> float` is provided (test stub returns fixed prices).  

---  

## 2. Backend – `trading_backend.py`  

### 2.1 Data Models (simple `@dataclass`es)

| Class | Purpose | Fields |
|-------|---------|--------|
| `Transaction` | Immutable record of a deposit, withdrawal, buy, or sell | `id: str`, `type: Literal["deposit","withdraw","buy","sell"]`, `symbol: str | None`, `quantity: float | None`, `price: float | None`, `amount: float` (cash moved), `timestamp: datetime` |
| `Holding` | Current position for a symbol | `symbol: str`, `quantity: float` |
| `UserAccount` | All state for a single user | `user_id: str`, `balance: float`, `initial_deposit: float`, `transactions: List[Transaction]`, `holdings: Dict[str, Holding]` |

*All classes are defined in `trading_backend.py` – **no external persistence** required for the prototype.*

### 2.2 Core Functions (public API)

```python
# trading_backend.py

from typing import List, Dict, Literal, Tuple
from datetime import datetime
from dataclasses import dataclass, field

# ----------------------------------------------------------------------
# Helper (provided)
def get_share_price(symbol: str) -> float:
    """Return current price for a symbol. Test implementation returns fixed values."""
    ...

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
    """Create a new account with zero balance. Raises if user already exists."""
    ...

def deposit_funds(user_id: str, amount: float) -> float:
    """Add cash to balance; updates initial_deposit on first deposit. Returns new balance."""
    ...

def withdraw_funds(user_id: str, amount: float) -> float:
    """Subtract cash if sufficient balance. Raises on insufficient funds. Returns new balance."""
    ...

# ----------------------------------------------------------------------
# Trading Operations
def buy_shares(user_id: str, symbol: str, quantity: float) -> Tuple[float, float]:
    """
    Purchase `quantity` shares of `symbol` at current price.
    Returns (total_cost, new_balance). Raises on insufficient cash.
    """
    ...

def sell_shares(user_id: str, symbol: str, quantity: float) -> Tuple[float, float]:
    """
    Sell `quantity` shares of `symbol` at current price.
    Returns (proceeds, new_balance). Raises on insufficient holdings.
    """
    ...

# ----------------------------------------------------------------------
# Portfolio Reporting
def get_holdings(user_id: str) -> List[Holding]:
    """Return a snapshot list of current holdings (symbol + quantity)."""
    ...

def get_portfolio_value(user_id: str) -> float:
    """Sum of cash balance + market value of all holdings (using `get_share_price`)."""
    ...

def get_profit_loss(user_id: str) -> float:
    """Portfolio value minus the initial deposit."""
    ...

def list_transactions(user_id: str) -> List[Transaction]:
    """Chronological list of all transactions for the user."""
    ...

# ----------------------------------------------------------------------
# Internal helpers (private)
def _record_transaction(account: UserAccount, tx: Transaction) -> None:
    """Append transaction and keep list sorted by timestamp."""
    ...

def _ensure_user(user_id: str) -> UserAccount:
    """Retrieve account or raise KeyError if not found."""
    ...
```

**Notes for backend_engineer**

* All functions must be **pure** (no side‑effects beyond the in‑memory store).  
* Use `uuid4().hex` for generating transaction IDs.  
* Raise `ValueError` with clear messages for business‑rule violations (negative balance, insufficient shares, invalid quantity, etc.).  
* Keep the module **import‑safe** – no code should execute on import.  

---  

## 3. Frontend – `app.py` (Gradio 6)  

### 3.1 General Guidance (Gradio 6 API)

* **App‑level parameters** (`theme`, `css`, …) are now passed to `demo.launch(...)`, **not** to `gr.Blocks()`.  
* Use **`with gr.Blocks() as demo:`** to compose the UI.  
* Event handling is performed via component methods (`.click`, `.submit`, `.change`).  
* The default `trigger_mode` for `.click()` is `"once"` – sufficient for our simple UI.  
* All backend functions are **synchronous**; Gradio will run them in a thread pool automatically.  

### 3.2 UI Layout (suggested)

| Tab | Purpose | Components |
|-----|---------|------------|
| **Account** | Create, deposit, withdraw | `Textbox` (user_id), `Number` (amount), `Button`s (Create, Deposit, Withdraw), `Markdown` for status |
| **Trade** | Buy / Sell shares | `Textbox` (user_id), `Dropdown` (symbol: AAPL, TSLA, GOOGL), `Number` (quantity), `Button`s (Buy, Sell), `Markdown` for result |
| **Portfolio** | View holdings & value | `Textbox` (user_id), `Button` (Refresh), `Dataframe` (holdings), `Markdown` (cash, total value, P/L) |
| **History** | Transaction log | `Textbox` (user_id), `Button` (Refresh), `Dataframe` (transactions) |

### 3.3 Example Function Signatures for UI Callbacks  

```python
# app.py (frontend)
import gradio as gr
from trading_backend import (
    create_account, deposit_funds, withdraw_funds,
    buy_shares, sell_shares,
    get_holdings, get_portfolio_value, get_profit_loss,
    list_transactions,
)

def ui_create_account(user_id: str) -> str:
    try:
        create_account(user_id)
        return f"✅ Account `{user_id}` created."
    except ValueError as e:
        return f"❌ {e}"

def ui_deposit(user_id: str, amount: float) -> str:
    try:
        new_bal = deposit_funds(user_id, amount)
        return f"✅ Deposited ${amount:.2f}. New balance: ${new_bal:.2f}"
    except Exception as e:
        return f"❌ {e}"

def ui_withdraw(user_id: str, amount: float) -> str:
    ...

def ui_buy(user_id: str, symbol: str, qty: float) -> str:
    ...

def ui_sell(user_id: str, symbol: str, qty: float) -> str:
    ...

def ui_refresh_portfolio(user_id: str) -> Tuple[str, str, str, List[Tuple[str, float]]]:
    """
    Returns (cash_md, value_md, pl_md, holdings_table)
    where holdings_table is a list of rows [(symbol, quantity), ...].
    """
    ...

def ui_refresh_history(user_id: str) -> List[Tuple]:
    """Return a list of rows for the Dataframe component."""
    ...
```

**Key Gradio 6 specifics to embed in the code (frontend_engineer):**

```python
with gr.Blocks() as demo:
    # ==== Account Tab ====
    with gr.Tab("Account"):
        user_id_acct = gr.Textbox(label="User ID")
        amount_acct = gr.Number(label="Amount", precision=2)
        btn_create = gr.Button("Create Account")
        btn_deposit = gr.Button("Deposit")
        btn_withdraw = gr.Button("Withdraw")
        acct_status = gr.Markdown()

        btn_create.click(fn=ui_create_account,
                         inputs=user_id_acct,
                         outputs=acct_status)

        btn_deposit.click(fn=ui_deposit,
                          inputs=[user_id_acct, amount_acct],
                          outputs=acct_status)

        btn_withdraw.click(fn=ui_withdraw,
                           inputs=[user_id_acct, amount_acct],
                           outputs=acct_status)

    # ==== Trade Tab ====
    with gr.Tab("Trade"):
        user_id_trade = gr.Textbox(label="User ID")
        symbol_dd = gr.Dropdown(choices=["AAPL", "TSLA", "GOOGL"], label="Symbol")
        qty_trade = gr.Number(label="Quantity", precision=4)
        btn_buy = gr.Button("Buy")
        btn_sell = gr.Button("Sell")
        trade_status = gr.Markdown()

        btn_buy.click(fn=ui_buy,
                      inputs=[user_id_trade, symbol_dd, qty_trade],
                      outputs=trade_status)

        btn_sell.click(fn=ui_sell,
                       inputs=[user_id_trade, symbol_dd, qty_trade],
                       outputs=trade_status)

    # ==== Portfolio Tab ====
    with gr.Tab("Portfolio"):
        user_id_port = gr.Textbox(label="User ID")
        btn_refresh_port = gr.Button("Refresh")
        cash_md = gr.Markdown()
        value_md = gr.Markdown()
        pl_md = gr.Markdown()
        holdings_df = gr.Dataframe(headers=["Symbol", "Quantity"], datatype=["str", "number"])

        btn_refresh_port.click(
            fn=ui_refresh_portfolio,
            inputs=user_id_port,
            outputs=[cash_md, value_md, pl_md, holdings_df],
        )

    # ==== History Tab ====
    with gr.Tab("History"):
        user_id_hist = gr.Textbox(label="User ID")
        btn_refresh_hist = gr.Button("Refresh")
        hist_df = gr.Dataframe(headers=["Time", "Type", "Symbol", "Qty", "Price", "Amount"])

        btn_refresh_hist.click(
            fn=ui_refresh_history,
            inputs=user_id_hist,
            outputs=hist_df,
        )

# Launch with app‑level settings moved to launch()
demo.launch(
    theme=gr.themes.Soft(),
    css="""
        .gradio-container {font-family: Arial, sans-serif;}
        .markdown {margin-top: 0.5rem;}
    """,
    server_port=7860,
    share=False,
)
```

*All component constructors (`Textbox`, `Number`, `Dropdown`, `Button`, `Dataframe`, `Markdown`) use the **new default parameter names** (e.g., `label`, `precision`).*  
*No legacy `Blocks(..., theme=..., css=...)` arguments are used – they belong in `demo.launch(...)` as shown.*  

---  

## 4. Tests – `test_trading_backend.py`  

### 4.1 Scope  

* **Account lifecycle** – creation, duplicate creation error.  
* **Deposit / Withdrawal** – normal flow, negative amount guard, insufficient‑balance guard.  
* **Buy / Sell** – price lookup, cash check, holding check, quantity validation, correct transaction recording.  
* **Portfolio calculations** – cash + market value, profit/loss after series of trades.  
* **Edge cases** – zero/negative quantity, unknown symbol, floating‑point rounding.  

### 4.2 Example Test Skeleton (test_engineer)

```python
# test_trading_backend.py
import pytest
from trading_backend import (
    create_account, deposit_funds, withdraw_funds,
    buy_shares, sell_shares,
    get_holdings, get_portfolio_value, get_profit_loss,
    list_transactions,
)

@pytest.fixture
def fresh_user():
    uid = "test_user"
    # Ensure a clean slate
    try:
        create