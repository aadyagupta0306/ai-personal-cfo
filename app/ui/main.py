import sys, os
sys.path.append(os.getcwd())

import streamlit as st
import plotly.express as px
from datetime import datetime

from app.services.transaction_service import (
    add_transaction,
    get_all_transactions,
)

from app.services.analytics_service import (
    get_transactions_df,
    get_summary,
    get_category_breakdown,
    get_monthly_trend,
)

from app.services.account_service import (
    add_account,
    get_all_accounts,
    get_account_balance,
)

from app.services.goal_service import (
    add_goal,
    get_all_goals,
    add_contribution,
)

from app.constants import (
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    PAYMENT_METHODS,
)
from app.services.budget_service import add_budget, get_budgets_for_month, get_spent_for_category

# --------------------------------------------------
# Page Config
# --------------------------------------------------

st.set_page_config(
    page_title="AI Personal CFO",
    page_icon="💰",
    layout="wide",
)

st.title("💰 AI Personal CFO")
st.caption("Your AI-powered financial operating system.")

# --------------------------------------------------
# ACCOUNTS (one-time onboarding)
# --------------------------------------------------

accounts = get_all_accounts()

if not accounts:
    st.header("🏦 Set Up Your Account")
    st.caption("Add your first account with its current balance to get started.")

    with st.form("add_account_form"):
        acc_name = st.text_input("Account Name", placeholder="e.g. HDFC Savings")
        acc_type = st.selectbox("Account Type", ["bank", "cash", "wallet"])
        acc_balance = st.number_input("Current Balance (₹)", min_value=0.0, step=100.0)

        if st.form_submit_button("Create Account"):
            add_account(acc_name, acc_type, acc_balance)
            st.rerun()

    st.stop()

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

df = get_transactions_df()

if not df.empty:
    income, expense, savings = get_summary(df)
else:
    income = expense = savings = 0

total_balance = sum(get_account_balance(a.id) for a in accounts)

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric("🏦 Current Balance", f"₹{total_balance:,.0f}")
metric2.metric("💰 Total Income", f"₹{income:,.0f}")
metric3.metric("💸 Total Expense", f"₹{expense:,.0f}")
metric4.metric("📈 Net Savings", f"₹{savings:,.0f}")

st.divider()

# --------------------------------------------------
# ADD TRANSACTION
# --------------------------------------------------

st.header("➕ Quick Add Transaction")

type_ = st.selectbox(
    "Type",
    ["expense", "income"],
)

categories = (
    EXPENSE_CATEGORIES
    if type_ == "expense"
    else INCOME_CATEGORIES
)

account_options = {a.name: a.id for a in accounts}

with st.form("add_txn_form"):

    amount = st.number_input(
        "Amount",
        min_value=0.0,
        step=10.0,
    )

    col1, col2 = st.columns(2)

    with col1:
        category = st.selectbox(
            "Category",
            categories,
        )

    with col2:
        payment_method = st.selectbox(
            "Payment Method",
            PAYMENT_METHODS,
        )

    col3, col4 = st.columns(2)

    with col3:
        date = st.date_input(
            "Date",
            value=datetime.now(),
        )

    with col4:
        selected_account = st.selectbox(
            "Account",
            list(account_options.keys()),
        )

    description = st.text_input(
        "Description (optional)",
        placeholder="e.g. Starbucks, Uber, Amazon...",
    )

    submitted = st.form_submit_button(
        "➕ Add Transaction",
        use_container_width=True,
    )

    if submitted:

        add_transaction(
            amount=amount,
            type=type_,
            category=category,
            date=datetime.combine(
                date,
                datetime.min.time(),
            ),
            account_id=account_options[selected_account],
            description=description or None,
            payment_method=payment_method,
        )

        st.success("✅ Transaction added!")
        st.rerun()

st.divider()

# --------------------------------------------------
# CHARTS
# --------------------------------------------------

st.header("📊 Analytics")

if not df.empty:

    breakdown = get_category_breakdown(
        df,
        "expense",
    )

    if not breakdown.empty:

        fig1 = px.pie(
            breakdown,
            names="category",
            values="amount",
            title="Expense Breakdown",
        )

        st.plotly_chart(
            fig1,
            use_container_width=True,
        )

    trend = get_monthly_trend(df)

    if not trend.empty:

        fig2 = px.bar(
            trend,
            x="month",
            y="amount",
            color="type",
            barmode="group",
            title="Monthly Income vs Expense",
        )

        st.plotly_chart(
            fig2,
            use_container_width=True,
        )

else:

    st.info(
        "Add your first transaction to start seeing analytics."
    )

st.divider()

# --------------------------------------------------
# GOALS
# --------------------------------------------------

st.header("🎯 Goals")

with st.expander("➕ Add New Goal"):
    with st.form("add_goal_form"):
        goal_name = st.text_input("Goal Name", placeholder="e.g. Goa Trip")
        goal_type = st.selectbox("Goal Type", ["trip", "purchase", "savings", "emergency_fund"])
        target_amount = st.number_input("Target Amount (₹)", min_value=0.0, step=500.0)
        target_date = st.date_input("Target Date")

        if st.form_submit_button("Create Goal"):
            add_goal(
                goal_name,
                goal_type,
                target_amount,
                datetime.combine(target_date, datetime.min.time()),
            )
            st.rerun()

goals = get_all_goals()

if goals:
    for g in goals:
        progress = min(g.current_amount / g.target_amount, 1.0) if g.target_amount else 0

        st.write(f"**{g.name}** — ₹{g.current_amount:,.0f} / ₹{g.target_amount:,.0f}")
        st.progress(progress)

        col1, col2 = st.columns([3, 1])

        with col1:
            contribution = st.number_input(
                f"Add to {g.name}",
                min_value=0.0,
                step=100.0,
                key=f"contrib_{g.id}",
            )

        with col2:
            st.write("")
            if st.button("Add", key=f"btn_{g.id}"):
                add_contribution(g.id, contribution)
                st.rerun()
else:
    st.info("No goals yet — add one above.")

st.divider()

# --------------------------------------------------
# RECENT TRANSACTIONS
# --------------------------------------------------

st.header("🧾 Recent Transactions")

transactions = get_all_transactions()

if transactions:

    st.dataframe(
        [
            {
                "Date": t.date.strftime("%Y-%m-%d"),
                "Type": t.type.title(),
                "Category": t.category,
                "Amount": f"₹{t.amount:,.0f}",
                "Description": t.description,
                "Payment": t.payment_method,
            }
            for t in transactions
        ],
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info("No transactions yet.")

#--------------------------------------------------
# BUDGETS
#--------------------------------------------------

st.header("📅 Budgets")

current_month = datetime.now().strftime("%Y-%m")

with st.expander("➕ Set / Update Budget"):
    with st.form("add_budget_form"):
        budget_category = st.selectbox("Category", EXPENSE_CATEGORIES)
        budget_amount = st.number_input("Monthly Budget (₹)", min_value=0.0, step=100.0)

        if st.form_submit_button("Save Budget"):
            add_budget(budget_category, budget_amount, current_month)
            st.rerun()

budgets = get_budgets_for_month(current_month)

if budgets:
    for b in budgets:
        spent = get_spent_for_category(b.category, current_month)
        progress = min(spent / b.amount, 1.0) if b.amount else 0
        remaining = b.amount - spent

        st.write(f"**{b.category}** — ₹{spent:,.0f} / ₹{b.amount:,.0f}")
        st.progress(progress)

        if spent > b.amount:
            st.error(f"Over budget by ₹{abs(remaining):,.0f}")
        elif progress > 0.8:
            st.warning(f"₹{remaining:,.0f} remaining — close to limit")
        else:
            st.caption(f"₹{remaining:,.0f} remaining")
else:
    st.info(f"No budgets set for {current_month} yet — add one above.")