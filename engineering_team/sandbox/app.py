"""Gradio interface for the in-memory trading account backend."""

from __future__ import annotations

import gradio as gr

from trading_backend import (
    buy_shares,
    create_account,
    deposit_funds,
    get_holdings,
    get_portfolio_value,
    get_profit_loss,
    list_transactions,
    sell_shares,
    withdraw_funds,
)


def ui_create_account(user_id: str) -> str:
    try:
        create_account(user_id.strip())
        return f"Account **{user_id.strip()}** created."
    except (ValueError, KeyError) as exc:
        return f"Could not create account: {exc}"


def ui_deposit(user_id: str, amount: float) -> str:
    try:
        balance = deposit_funds(user_id.strip(), amount)
        return f"Deposited **${amount:,.2f}** · New cash balance **${balance:,.2f}**"
    except (ValueError, KeyError, TypeError) as exc:
        return f"Deposit failed: {exc}"


def ui_withdraw(user_id: str, amount: float) -> str:
    try:
        balance = withdraw_funds(user_id.strip(), amount)
        return f"Withdrew **${amount:,.2f}** · New cash balance **${balance:,.2f}**"
    except (ValueError, KeyError, TypeError) as exc:
        return f"Withdrawal failed: {exc}"


def ui_trade(user_id: str, symbol: str, quantity: float, action: str) -> str:
    try:
        if action == "buy":
            amount, balance = buy_shares(user_id.strip(), symbol, quantity)
            return f"Bought **{quantity:g} {symbol}** for **${amount:,.2f}** · Cash **${balance:,.2f}**"
        amount, balance = sell_shares(user_id.strip(), symbol, quantity)
        return f"Sold **{quantity:g} {symbol}** for **${amount:,.2f}** · Cash **${balance:,.2f}**"
    except (ValueError, KeyError, TypeError) as exc:
        return f"Trade failed: {exc}"


def ui_portfolio(user_id: str) -> tuple[list[list[object]], str]:
    try:
        holdings = get_holdings(user_id.strip())
        rows = [[holding.symbol, holding.quantity] for holding in holdings]
        account_value = get_portfolio_value(user_id.strip())
        profit_loss = get_profit_loss(user_id.strip())
        sign = "+" if profit_loss >= 0 else "−"
        summary = (
            f"### Portfolio value: ${account_value:,.2f}\n"
            f"**Profit / loss:** {sign}${abs(profit_loss):,.2f}"
        )
        return rows, summary
    except KeyError as exc:
        return [], f"Account not found: {exc}"


def ui_history(user_id: str) -> list[list[object]]:
    try:
        return [
            [tx.timestamp.isoformat(timespec="seconds"), tx.type, tx.symbol or "—",
             tx.quantity if tx.quantity is not None else "—", f"${tx.amount:,.2f}"]
            for tx in list_transactions(user_id.strip())
        ]
    except KeyError:
        return []


CSS = """
.gradio-container { max-width: 1080px !important; }
.hero { padding: 1.5rem 1.7rem; border-radius: 18px; margin-bottom: 1rem;
        background: linear-gradient(120deg, #209dd71c, #75399112); }
.hero h1 { margin: 0 0 .35rem 0; }
.hint { opacity: .75; }
button.primary { background: #209dd7 !important; border-color: #209dd7 !important; }
"""

THEME = gr.themes.Soft(
    primary_hue="sky", secondary_hue="purple", neutral_hue="slate"
)

with gr.Blocks(title="Northstar · Trading Simulator") as demo:
    gr.Markdown(
        "# Northstar Trading Simulator\n"
        "Practice account management and trading with fixed AAPL, TSLA, and GOOGL prices.",
        elem_classes=["hero"],
    )

    with gr.Tabs():
        with gr.Tab("Account"):
            gr.Markdown("Create an account, then add or withdraw cash.")
            account_user = gr.Textbox(label="Account ID", placeholder="e.g. alex")
            with gr.Row():
                create_button = gr.Button("Create account", variant="primary")
                account_status = gr.Markdown()
            create_button.click(ui_create_account, inputs=account_user, outputs=account_status)
            gr.Markdown("#### Cash activity")
            with gr.Row():
                cash_amount = gr.Number(label="Amount ($)", minimum=0, value=1000, precision=2)
                deposit_button = gr.Button("Deposit")
                withdraw_button = gr.Button("Withdraw")
            cash_status = gr.Markdown()
            deposit_button.click(ui_deposit, inputs=[account_user, cash_amount], outputs=cash_status)
            withdraw_button.click(ui_withdraw, inputs=[account_user, cash_amount], outputs=cash_status)

        with gr.Tab("Trade"):
            trade_user = gr.Textbox(label="Account ID", placeholder="Use your account ID")
            with gr.Row():
                symbol = gr.Dropdown(["AAPL", "TSLA", "GOOGL"], value="AAPL", label="Symbol")
                quantity = gr.Number(label="Shares", minimum=0, value=1, precision=4)
            with gr.Row():
                buy_button = gr.Button("Buy shares", variant="primary")
                sell_button = gr.Button("Sell shares")
            trade_status = gr.Markdown()
            buy_button.click(lambda uid, ticker, qty: ui_trade(uid, ticker, qty, "buy"),
                             inputs=[trade_user, symbol, quantity], outputs=trade_status)
            sell_button.click(lambda uid, ticker, qty: ui_trade(uid, ticker, qty, "sell"),
                              inputs=[trade_user, symbol, quantity], outputs=trade_status)

        with gr.Tab("Portfolio"):
            portfolio_user = gr.Textbox(label="Account ID", placeholder="Use your account ID")
            refresh_portfolio = gr.Button("Refresh portfolio", variant="primary")
            portfolio_summary = gr.Markdown()
            holdings = gr.Dataframe(headers=["Symbol", "Shares"], label="Holdings", interactive=False)
            refresh_portfolio.click(ui_portfolio, inputs=portfolio_user,
                                    outputs=[holdings, portfolio_summary])

        with gr.Tab("History"):
            history_user = gr.Textbox(label="Account ID", placeholder="Use your account ID")
            refresh_history = gr.Button("Refresh transactions", variant="primary")
            history = gr.Dataframe(
                headers=["Time", "Type", "Symbol", "Quantity", "Cash movement"],
                label="Transaction history",
                interactive=False,
            )
            refresh_history.click(ui_history, inputs=history_user, outputs=history)


if __name__ == "__main__":
    demo.launch(theme=THEME, css=CSS)
