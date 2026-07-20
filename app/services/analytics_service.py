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

from datetime import datetime, timedelta

def filter_by_period(df, period="week"):
    if df.empty:
        return df
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    now = datetime.now()

    if period == "week":
        start = now - timedelta(days=7)
    else:  # month
        start = now.replace(day=1)

    return df[df["date"] >= start]

def get_month_over_month_comparison(df):
    if df.empty:
        return pd.DataFrame(columns=["category", "this_month", "last_month", "change_pct"])

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    now = datetime.now()
    this_month_start = now.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

    expenses = df[df["type"] == "expense"]

    this_month = expenses[expenses["date"] >= this_month_start].groupby("category")["amount"].sum()
    last_month = expenses[(expenses["date"] >= last_month_start) & (expenses["date"] < this_month_start)].groupby("category")["amount"].sum()

    comparison = pd.DataFrame({"this_month": this_month, "last_month": last_month}).fillna(0).reset_index()
    comparison["change_pct"] = comparison.apply(
        lambda row: ((row["this_month"] - row["last_month"]) / row["last_month"] * 100) if row["last_month"] > 0 else (100 if row["this_month"] > 0 else 0),
        axis=1
    )
    return comparison