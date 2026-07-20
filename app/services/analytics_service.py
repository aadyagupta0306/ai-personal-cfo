import pandas as pd
from app.services.transaction_service import get_all_transactions

def get_transactions_df():
    transactions = get_all_transactions()
    data = [{
        "date": t.date,
        "type": t.type,
        "category": t.category,
        "amount": t.amount,
    } for t in transactions]
    return pd.DataFrame(data)

def get_summary(df):
    total_income = df[df["type"] == "income"]["amount"].sum()
    total_expense = df[df["type"] == "expense"]["amount"].sum()
    net_savings = total_income - total_expense
    return total_income, total_expense, net_savings

def get_category_breakdown(df, type_="expense"):
    filtered = df[df["type"] == type_]
    return filtered.groupby("category")["amount"].sum().reset_index()

def get_monthly_trend(df):
    df = df.copy()
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
    return df.groupby(["month", "type"])["amount"].sum().reset_index()