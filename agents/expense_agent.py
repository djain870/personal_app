from database import SessionLocal
from models import Expense

def run(user, message):
    db = SessionLocal()
    expenses = db.query(Expense).filter(Expense.user == user).all()
    db.close()

    expense_text = "\n".join(
        [f"{e.category} - ₹{e.amount} on {e.date}" for e in expenses]
    )

    return f"""
You are a finance assistant.

User expenses:
{expense_text}

Question:
{message}
"""