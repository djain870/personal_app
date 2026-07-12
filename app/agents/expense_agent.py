from app.db.session import SessionLocal
from app.models import Cashflow, Expense, Wealth


def format_money(value):
    return f"₹{value:,.2f}"


def format_expenses(expenses):
    if not expenses:
        return "No expense records found."

    return "\n".join(
        [
            f"- {e.date}: {e.category} | {format_money(e.amount)} | {e.note or 'No note'}"
            for e in expenses
        ]
    )


def summarize_wealth(wealth_rows):
    if not wealth_rows:
        return "No wealth records found."

    monthly_totals = {}
    allocation_totals = {}

    for row in wealth_rows:
        month = row.month.strftime("%Y-%m")
        monthly_totals[month] = monthly_totals.get(month, 0) + row.balance
        allocation_totals[row.type] = allocation_totals.get(row.type, 0) + row.balance

    monthly_summary = "\n".join(
        [f"- {month}: net worth {format_money(total)}" for month, total in sorted(monthly_totals.items())]
    )
    allocation_summary = "\n".join(
        [f"- {asset_type}: {format_money(total)}" for asset_type, total in sorted(allocation_totals.items())]
    )

    recent_rows = sorted(wealth_rows, key=lambda row: row.month, reverse=True)[:20]
    recent_details = "\n".join(
        [
            f"- {row.month}: {row.account} | {row.type} | {row.volatility} | {format_money(row.balance)}"
            for row in recent_rows
        ]
    )

    return f"""
Monthly net worth:
{monthly_summary}

Asset allocation totals:
{allocation_summary}

Recent wealth records:
{recent_details}
"""


def summarize_cashflow(cashflow_rows):
    if not cashflow_rows:
        return "No cashflow records found."

    monthly = {}

    for row in cashflow_rows:
        month = row.month.strftime("%Y-%m")
        if month not in monthly:
            monthly[month] = {"Income": 0, "Expense": 0, "Savings": 0}
        monthly[month][row.flag] = monthly[month].get(row.flag, 0) + row.amount

    monthly_summary = "\n".join(
        [
            (
                f"- {month}: income {format_money(values.get('Income', 0))}, "
                f"expenses {format_money(values.get('Expense', 0))}, "
                f"savings {format_money(values.get('Savings', 0))}"
            )
            for month, values in sorted(monthly.items())
        ]
    )

    recent_rows = sorted(cashflow_rows, key=lambda row: row.month, reverse=True)[:30]
    recent_details = "\n".join(
        [
            f"- {row.month}: {row.flag} | {row.type1} | {row.type} | {format_money(row.amount)}"
            for row in recent_rows
        ]
    )

    return f"""
Monthly cashflow:
{monthly_summary}

Recent cashflow records:
{recent_details}
"""

def run(user, message):
    db = SessionLocal()
    expenses = db.query(Expense).filter(Expense.user == user).all()
    wealth_rows = db.query(Wealth).filter(Wealth.user == user).all()
    cashflow_rows = db.query(Cashflow).filter(Cashflow.user == user).all()
    db.close()

    expense_text = format_expenses(expenses)
    wealth_text = summarize_wealth(wealth_rows)
    cashflow_text = summarize_cashflow(cashflow_rows)

    return f"""
You are a finance assistant.
Use the user's finance records below to answer questions about expenses, wealth, net worth, income, savings, and cashflow.
If the answer is not available in these records, say that the available data does not contain enough information.

User expenses:
{expense_text}

User wealth:
{wealth_text}

User cashflow:
{cashflow_text}

Question:
{message}
"""
