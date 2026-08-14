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

def build_balance_projection(current_balance, forecast_items):
    if not forecast_items:
        return pd.DataFrame([{"date": datetime.now(), "balance": current_balance}])

    sorted_items = sorted(forecast_items, key=lambda x: x["date"])
    rows = [{"date": datetime.now(), "balance": current_balance}]
    running = current_balance

    for item in sorted_items:
        running += item["amount"] if item["type"] == "income" else -item["amount"]
        rows.append({"date": item["date"], "balance": running})

    return pd.DataFrame(rows)

def get_dashboard_insights(df):
    insights = []

    if df.empty:
        return insights

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    expenses = df[df["type"] == "expense"]
    income = df[df["type"] == "income"]

    # Biggest spending category (all-time)
    if not expenses.empty:
        top_category = expenses.groupby("category")["amount"].sum().idxmax()
        top_amount = expenses.groupby("category")["amount"].sum().max()
        insights.append(f"📊 Your biggest spending category is **{top_category}** (₹{top_amount:,.0f} total)")

    # Largest single transaction
    if not expenses.empty:
        largest = expenses.loc[expenses["amount"].idxmax()]
        insights.append(f"💸 Your largest expense was ₹{largest['amount']:,.0f} on {largest['category']} ({largest['date'].strftime('%b %d')})")

    # Unusual spending: today/this week vs category average
    if not expenses.empty:
        avg_txn = expenses["amount"].mean()
        recent = expenses[expenses["date"] >= datetime.now() - timedelta(days=7)]
        unusual = recent[recent["amount"] > avg_txn * 2]
        if not unusual.empty:
            row = unusual.iloc[0]
            insights.append(f"⚠️ Unusual spending detected: ₹{row['amount']:,.0f} on {row['category']} — more than double your average transaction")

    # Savings rate
    total_income = income["amount"].sum()
    total_expense = expenses["amount"].sum()
    if total_income > 0:
        savings_rate = ((total_income - total_expense) / total_income) * 100
        insights.append(f"🏦 Your overall savings rate is **{savings_rate:.0f}%** of income")

    # Income stability: variation across income transactions
    if len(income) >= 2:
        income_std = income["amount"].std()
        income_mean = income["amount"].mean()
        variability = (income_std / income_mean) * 100 if income_mean else 0
        stability_label = "stable" if variability < 30 else "variable"
        insights.append(f"📈 Your income is **{stability_label}** (varies by ~{variability:.0f}% across sources)")

    return insights

def build_financial_timeline(transactions, expected_items, goals, days_back=14, days_forward=45):
    now = datetime.now()
    window_start = now - timedelta(days=days_back)
    window_end = now + timedelta(days=days_forward)

    events = []

    for t in transactions:
        if window_start <= t.date <= window_end:
            events.append({
                "date": t.date,
                "label": t.description or t.category,
                "amount": t.amount,
                "type": t.type,
                "kind": "transaction",
                "status": "happened",
            })

    for e in expected_items:
        if e.status == "pending" and window_start <= e.expected_date <= window_end:
            events.append({
                "date": e.expected_date,
                "label": e.label,
                "amount": e.amount,
                "type": e.type,
                "kind": "expected",
                "status": "pending",
            })

    for g in goals:
        if g.target_date and window_start <= g.target_date <= window_end:
            events.append({
                "date": g.target_date,
                "label": f"Goal deadline: {g.name}",
                "amount": g.target_amount - g.current_amount,
                "type": "goal",
                "kind": "goal",
                "status": "upcoming",
            })

    events.sort(key=lambda e: e["date"])
    return events

def get_proactive_alerts(budgets_status, goals, forecast_projection_df, forecast_items):
    alerts = []

    for b in budgets_status:
        if b["velocity"]["spent"] > b["amount"]:
            alerts.append(f"{b['category']} budget is already exceeded by ₹{b['velocity']['spent'] - b['amount']:,.0f}")
        elif b["velocity"]["will_exceed"]:
            alerts.append(f"{b['category']} is on pace to exceed budget by month end (safe spend: ₹{b['velocity']['safe_daily_spend']:,.0f}/day)")

    for g in goals:
        from app.services.goal_service import get_goal_pacing
        pacing = get_goal_pacing(g)
        if pacing:
            if pacing["status"] == "overdue" and pacing["amount_remaining"] > 0:
                alerts.append(f"Goal '{g.name}' target date has passed, still ₹{pacing['amount_remaining']:,.0f} short")

    if not forecast_projection_df.empty:
        lowest = forecast_projection_df["balance"].min()
        if lowest < 0:
            alerts.append(f"Projected balance goes negative (as low as ₹{lowest:,.0f}) within 90 days based on current commitments")

    upcoming_7d = [f for f in forecast_items if (f["date"] - datetime.now()).days <= 7 and f["type"] == "expense"]
    if upcoming_7d:
        total_due = sum(f["amount"] for f in upcoming_7d)
        alerts.append(f"₹{total_due:,.0f} in expected payments due within the next 7 days ({', '.join(f['label'] for f in upcoming_7d)})")

    return alerts

def get_behavior_analysis(df):
    if df.empty:
        return {}

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    expenses = df[df["type"] == "expense"].copy()

    if expenses.empty:
        return {}

    # Category trend: compare last 30 days vs prior 30 days
    now = datetime.now()
    recent_30 = expenses[expenses["date"] >= now - timedelta(days=30)]
    prior_30 = expenses[(expenses["date"] >= now - timedelta(days=60)) & (expenses["date"] < now - timedelta(days=30))]

    recent_by_cat = recent_30.groupby("category")["amount"].sum()
    prior_by_cat = prior_30.groupby("category")["amount"].sum()

    trends = []
    for cat in set(list(recent_by_cat.index) + list(prior_by_cat.index)):
        r = recent_by_cat.get(cat, 0)
        p = prior_by_cat.get(cat, 0)
        if p > 0:
            change = ((r - p) / p) * 100
        elif r > 0:
            change = 100
        else:
            continue
        trends.append({"category": cat, "recent": r, "prior": p, "change_pct": change})

    trends.sort(key=lambda x: abs(x["change_pct"]), reverse=True)

    # Weekday vs weekend
    expenses["is_weekend"] = expenses["date"].dt.dayofweek >= 5
    weekend_avg = expenses[expenses["is_weekend"]]["amount"].mean() or 0
    weekday_avg = expenses[~expenses["is_weekend"]]["amount"].mean() or 0

    # Most frequent descriptions (recurring-looking spend)
    if "description" in expenses.columns:
        freq = expenses["description"].dropna().value_counts().head(5)
        frequent_items = [{"description": desc, "count": count} for desc, count in freq.items()]
    else:
        frequent_items = []

    return {
        "category_trends": trends[:5],
        "weekend_avg": weekend_avg,
        "weekday_avg": weekday_avg,
        "frequent_items": frequent_items,
    }
