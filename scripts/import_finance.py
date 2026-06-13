import pandas as pd
import re

from app.db.session import SessionLocal

from app.db.session import engine
from app.models import Base, Cashflow, Wealth

Base.metadata.create_all(bind=engine)

file_path = "master_finance.xlsx"

df_wealth = pd.read_excel(file_path, sheet_name='Totals').iloc[:, :5]
df_cashflow = pd.read_excel(file_path, sheet_name='Transactions').iloc[:, :5]

df_wealth.columns = ["Month", "Account", "Type", "Balance", "Volatility"]
df_cashflow.columns = ["Month", "Type1", "Type", "Amount", "Flag"]


print(df_wealth.head())
print(df_cashflow.head())



db = SessionLocal()

# Clear existing data to avoid duplicates
db.query(Wealth).delete()
db.query(Cashflow).delete()
db.commit()

# Insert wealth data
for _, row in df_wealth.iterrows():
    try:
        month = pd.to_datetime(row["Month"], format="%b-%y").date()

        entry = Wealth(
            month=month,
            account=row["Account"],
            type=row["Type"],
            balance=row["Balance"],
            volatility=row["Volatility"],
            user="Divyansh"
        )

        db.add(entry)

    except Exception as e:
        print("Skipping wealth row:", e)

# Insert cashflow data
for _, row in df_cashflow.iterrows():
    try:
        month = pd.to_datetime(row["Month"], format="%b-%y").date()

        entry = Cashflow(
            month=month,
            type1=row["Type1"],
            type=row["Type"],
            amount=row["Amount"],
            flag=row["Flag"],
            user="Divyansh"
        )

        db.add(entry)

    except Exception as e:
        print("Skipping cashflow row:", e)

db.commit()
db.close()

print("✅ Wealth and Cashflow data inserted successfully")
