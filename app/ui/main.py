import sys, os
sys.path.append(os.getcwd())

import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime

from app.services.transaction_service import add_transaction, get_all_transactions
from app.services.analytics_service import (
    get_transactions_df, get_summary, get_category_breakdown, get_monthly_trend,
    get_dashboard_insights, build_balance_projection, filter_by_period,
    get_month_over_month_comparison, build_financial_timeline,
)
from app.services.account_service import add_account, get_all_accounts, get_account_balance
from app.services.goal_service import add_goal, get_all_goals, add_contribution, get_goal_pacing
from app.services.budget_service import add_budget, get_budgets_for_month, get_spent_for_category, get_budget_velocity
from app.services.expected_transaction_service import (
    add_expected_transaction, get_all_expected, mark_status, get_forecast, get_pending_for_matching,
)
from app.services.chat_service import save_message, get_recent_history, get_context_for_chat, maybe_update_summary
from app.services.simulation_service import simulate_scenario
from app.models.expected_transaction import ExpectedTransaction
from app.database.session import SessionLocal
from app.constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES, PAYMENT_METHODS
from app.ai.transaction_parser import parse_transaction, validate_parsed
from app.ai.summary_generator import generate_summary
from app.ai.insight_generator import build_insight_facts, generate_insights
from app.ai.chat_assistant import chat_with_cfo
from app.ai.decision_narrator import explain_scenario

# --------------------------------------------------
# Page Config
# --------------------------------------------------

st.set_page_config(page_title="AI Personal CFO", layout="wide")
st.title("Personal Finance System")
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
# SHARED VARIABLES
# --------------------------------------------------

account_options = {a.name: a.id for a in accounts}
current_month = datetime.now().strftime("%Y-%m")
goals = get_all_goals()
df = get_transactions_df()

if not df.empty:
    income, expense, savings = get_summary(df)
else:
    income = expense = savings = 0

total_balance = sum(get_account_balance(a.id) for a in accounts)

if "whatif_events" not in st.session_state:
    st.session_state["whatif_events"] = []

# --------------------------------------------------
# INCOME → GOAL SUGGESTION BANNER
# --------------------------------------------------

if "income_logged" in st.session_state:
    logged = st.session_state["income_logged"]
    active_goals = [g for g in goals if g.current_amount < g.target_amount]

    st.info(f"💡 You received ₹{logged['amount']:,.0f}. Would you like to allocate some of it to a goal?")

    if active_goals:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            goal_names = {g.name: g.id for g in active_goals}
            chosen_goal_name = st.selectbox("Allocate to", list(goal_names.keys()), key="banner_goal_choice")
        with col2:
            suggested_default = round(logged["amount"] * 0.2, -1)
            allocate_amount = st.number_input(
                "Amount (₹)", min_value=0.0, value=suggested_default, step=100.0, key="banner_amount"
            )
        with col3:
            st.write("")
            if st.button("✅ Allocate"):
                add_contribution(goal_names[chosen_goal_name], allocate_amount)
                del st.session_state["income_logged"]
                st.success("Allocated!")
                st.rerun()

    if st.button("No thanks, dismiss"):
        del st.session_state["income_logged"]
        st.rerun()

    st.divider()

# --------------------------------------------------
# TOP METRICS (always visible)
# --------------------------------------------------

metric1, metric2, metric3, metric4 = st.columns(4)
metric1.metric("🏦 Current Balance", f"₹{total_balance:,.0f}")
metric2.metric("💰 Total Income", f"₹{income:,.0f}")
metric3.metric("💸 Total Expense", f"₹{expense:,.0f}")
metric4.metric("📈 Net Savings", f"₹{savings:,.0f}")

st.divider()

# --------------------------------------------------
# TABS
# --------------------------------------------------

tab_dashboard, tab_chat, tab_whatif, tab_transactions, tab_goals, tab_budgets, tab_upcoming = st.tabs(
    ["🏠 Dashboard", "💬 Ask CFO", "🧠 What-If", "➕ Transactions", "🎯 Goals", "📅 Budgets", "🔮 Upcoming"]
)

# ==================================================
# TAB: DASHBOARD
# ==================================================
with tab_dashboard:

    st.header("🤖 AI Quick Entry")
    nl_input = st.text_input("Describe a transaction", placeholder="e.g. spent 300 on uber yesterday")

    if st.button("Parse"):
        try:
            pending = get_pending_for_matching()
            parsed = parse_transaction(nl_input, pending)

            matched_id = parsed.get("matched_expected_id")
            if matched_id:
                session = SessionLocal()
                matched_item = session.query(ExpectedTransaction).filter(ExpectedTransaction.id == matched_id).first()
                session.close()
                if matched_item:
                    parsed["amount"] = matched_item.amount
                    parsed["type"] = matched_item.type
                    parsed["category"] = matched_item.category
                    parsed["date"] = matched_item.expected_date.strftime("%Y-%m-%d")
                    parsed["description"] = matched_item.label

            errors = validate_parsed(parsed)
            if errors:
                parsed = parse_transaction(nl_input, pending)
                errors = validate_parsed(parsed)

            st.session_state["ai_parsed"] = parsed
            st.session_state["ai_errors"] = errors
            st.session_state["ai_matched_id"] = matched_id
        except Exception as e:
            st.error(f"Couldn't parse that: {e}")

    if "ai_parsed" in st.session_state:
        parsed = st.session_state["ai_parsed"]
        errors = st.session_state["ai_errors"]

        if st.session_state.get("ai_matched_id"):
            st.info("✅ Matched to your pending expected transaction — using its recorded amount and date.")

        st.write("**Parsed result:**", parsed)

        if errors:
            st.warning("Issues found: " + ", ".join(errors))
        else:
            ai_acc_name = st.selectbox("Save to account", list(account_options.keys()), key="ai_account")
            if st.button("✅ Confirm & Save"):
                add_transaction(
                    amount=parsed["amount"], type=parsed["type"], category=parsed["category"],
                    date=datetime.strptime(parsed["date"], "%Y-%m-%d"), account_id=account_options[ai_acc_name],
                    description=parsed.get("description"), payment_method="Other",
                )
                st.success("Saved!")
                del st.session_state["ai_parsed"]
                if parsed["type"] == "income":
                    st.session_state["income_logged"] = {"amount": parsed["amount"]}
                st.rerun()

    st.divider()

    insights = get_dashboard_insights(df)
    if insights:
        st.subheader("🔍 What This Means")
        for insight in insights:
            st.write(insight)
        st.divider()

    st.subheader("📈 Balance Forecast (Next 90 Days)")
    forecast_items = get_forecast(90)
    projection_df = build_balance_projection(total_balance, forecast_items)
    fig_forecast = px.line(projection_df, x="date", y="balance", markers=True, title="Projected Balance Over Time")
    st.plotly_chart(fig_forecast, use_container_width=True)

    if forecast_items:
        lowest_point = min(projection_df["balance"])
        if lowest_point < 0:
            st.error(f"⚠️ Your projected balance goes negative (as low as ₹{lowest_point:,.0f}) based on current commitments.")

    st.subheader("🗓️ Financial Timeline")
    all_transactions = get_all_transactions()
    all_expected = get_all_expected()
    timeline_events = build_financial_timeline(all_transactions, all_expected, goals)

    if timeline_events:
        for e in timeline_events:
            is_past = e["date"] < datetime.now()
            date_str = e["date"].strftime("%b %d")
            icon = "✅" if e["kind"] == "transaction" else ("🔮" if e["kind"] == "expected" else "🎯")
            sign = "+" if e["type"] == "income" else ("-" if e["kind"] != "goal" else "")
            line = f"{icon} **{date_str}** — {e['label']} — {sign}₹{abs(e['amount']):,.0f}"

            if is_past:
                st.caption(line)
            else:
                st.write(line)
    else:
        st.info("No timeline events in this window.")

    st.subheader("📊 Analytics")
    if not df.empty:
        breakdown = get_category_breakdown(df, "expense")
        if not breakdown.empty:
            fig1 = px.pie(breakdown, names="category", values="amount", title="Expense Breakdown")
            st.plotly_chart(fig1, use_container_width=True)

        trend = get_monthly_trend(df)
        if not trend.empty:
            fig2 = px.bar(trend, x="month", y="amount", color="type", barmode="group", title="Monthly Income vs Expense")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Add your first transaction to start seeing analytics.")

    st.subheader("📝 AI Summary")
    period_choice = st.radio("Period", ["This Week", "This Month"], horizontal=True)
    period_key = "week" if period_choice == "This Week" else "month"

    if st.button("Generate Summary"):
        period_df = filter_by_period(df, period_key)
        if period_df.empty:
            st.info("No transactions in this period yet.")
        else:
            p_income, p_expense, p_savings = get_summary(period_df)
            p_breakdown = get_category_breakdown(period_df, "expense")
            with st.spinner("Thinking..."):
                summary_text = generate_summary(period_choice, p_income, p_expense, p_savings, p_breakdown)
            st.write(summary_text)

    st.subheader("💡 AI Insights")
    if st.button("Generate Insights"):
        comparison_df = get_month_over_month_comparison(df)
        current_budgets_for_insight = get_budgets_for_month(current_month)
        budgets_status = [
            {"category": b.category, "budget": b.amount, "spent": get_spent_for_category(b.category, current_month)}
            for b in current_budgets_for_insight
        ]
        facts = build_insight_facts(comparison_df, budgets_status)
        with st.spinner("Analyzing..."):
            insight_text = generate_insights(facts)
        st.write(insight_text)

    st.subheader("🧾 Recent Transactions")
    transactions = get_all_transactions()
    if transactions:
        st.dataframe(
            [
                {
                    "Date": t.date.strftime("%Y-%m-%d"), "Type": t.type.title(), "Category": t.category,
                    "Amount": f"₹{t.amount:,.0f}", "Description": t.description, "Payment": t.payment_method,
                }
                for t in transactions
            ],
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No transactions yet.")

# ==================================================
# TAB: ASK CFO (CHAT)
# ==================================================
with tab_chat:
    st.header("💬 Ask Your CFO")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = get_recent_history(10)

    for turn in st.session_state["chat_history"]:
        with st.chat_message(turn["role"]):
            st.write(turn["content"])

    user_msg = st.chat_input("Ask about your finances...")

    if user_msg:
        st.session_state["chat_history"].append({"role": "user", "content": user_msg})
        save_message("user", user_msg)

        summary_text, recent = get_context_for_chat()

        with st.spinner("Thinking..."):
            reply = chat_with_cfo(user_msg, summary_text, recent)

        st.session_state["chat_history"].append({"role": "assistant", "content": reply})
        save_message("assistant", reply)
        maybe_update_summary()
        st.rerun()

# ==================================================
# TAB: WHAT-IF SIMULATOR
# ==================================================
with tab_whatif:
    st.header("🧠 What-If Scenario")
    st.caption("Add one or more hypothetical purchases/income and ask if it's a good idea.")

    wf_type = st.selectbox("Type", ["expense", "income"], key="wf_type")
    wf_categories = EXPENSE_CATEGORIES if wf_type == "expense" else INCOME_CATEGORIES

    with st.form("whatif_add_event"):
        col1, col2, col3 = st.columns(3)
        with col1:
            wf_category = st.selectbox("Category", wf_categories, key="wf_cat")
        with col2:
            wf_amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, key="wf_amt")
        with col3:
            wf_date = st.date_input("Date", key="wf_date")

        wf_label = st.text_input("Label", placeholder="e.g. New headphones", key="wf_label")

        wf_submitted = st.form_submit_button("➕ Add to scenario")

    if wf_submitted:
        st.session_state["whatif_events"].append({
            "type": wf_type, "category": wf_category, "amount": wf_amount,
            "date": datetime.combine(wf_date, datetime.min.time()), "label": wf_label or wf_category,
        })
        st.success(f"✅ Added '{wf_label or wf_category}' to the scenario.")
        st.rerun()

    if st.session_state["whatif_events"]:
        st.write("**Scenario events:**")
        for i, ev in enumerate(st.session_state["whatif_events"]):
            sign = "+" if ev["type"] == "income" else "-"
            st.write(f"{i+1}. {ev['label']} — {sign}₹{ev['amount']:,.0f} on {ev['date'].strftime('%b %d')}")

        if st.button("🗑️ Clear scenario"):
            st.session_state["whatif_events"] = []
            st.rerun()

    question_text = st.text_area("Your question", placeholder="e.g. Can I afford both of these and still hit my Munnar goal?")

    if st.button("🔮 Run Scenario") and st.session_state["whatif_events"]:
        forecast_items_wf = get_forecast(90)
        facts = simulate_scenario(st.session_state["whatif_events"], total_balance, forecast_items_wf, goals)

        proj_df = pd.DataFrame(facts["timeline"])
        fig_wf = px.line(proj_df, x="date", y="balance", markers=True, title="Projected Balance With This Scenario")
        st.plotly_chart(fig_wf, use_container_width=True)

        with st.spinner("Analyzing..."):
            answer = explain_scenario(facts, question_text or "Can I afford this?")
        st.success(answer)

# ==================================================
# TAB: TRANSACTIONS
# ==================================================
with tab_transactions:
    st.header("➕ Quick Add Transaction")

    txn_type = st.selectbox("Type", ["expense", "income"], key="txn_type_select")
    txn_categories = EXPENSE_CATEGORIES if txn_type == "expense" else INCOME_CATEGORIES

    with st.form("add_txn_form"):
        txn_amount = st.number_input("Amount", min_value=0.0, step=10.0)

        col1, col2 = st.columns(2)
        with col1:
            txn_category = st.selectbox("Category", txn_categories)
        with col2:
            txn_payment_method = st.selectbox("Payment Method", PAYMENT_METHODS)

        col3, col4 = st.columns(2)
        with col3:
            txn_date = st.date_input("Date", value=datetime.now())
        with col4:
            txn_account_name = st.selectbox("Account", list(account_options.keys()))

        txn_description = st.text_input("Description (optional)", placeholder="e.g. Starbucks, Uber, Amazon...")
        txn_submitted = st.form_submit_button("➕ Add Transaction", use_container_width=True)

    if txn_submitted:
        add_transaction(
            amount=txn_amount, type=txn_type, category=txn_category,
            date=datetime.combine(txn_date, datetime.min.time()), account_id=account_options[txn_account_name],
            description=txn_description or None, payment_method=txn_payment_method,
        )
        st.success("✅ Transaction added!")
        if txn_type == "income":
            st.session_state["income_logged"] = {"amount": txn_amount}
        st.rerun()

# ==================================================
# TAB: GOALS
# ==================================================
with tab_goals:
    st.header("🎯 Goals")

    with st.expander("➕ Add New Goal"):
        with st.form("add_goal_form"):
            goal_name = st.text_input("Goal Name", placeholder="e.g. Goa Trip")
            goal_type = st.selectbox("Goal Type", ["trip", "purchase", "savings", "emergency_fund"])
            target_amount = st.number_input("Target Amount (₹)", min_value=0.0, step=500.0)
            target_date = st.date_input("Target Date")
            goal_submitted = st.form_submit_button("Create Goal")

    if goal_submitted:
        add_goal(goal_name, goal_type, target_amount, datetime.combine(target_date, datetime.min.time()))
        st.rerun()

    if goals:
        for g in goals:
            progress = min(g.current_amount / g.target_amount, 1.0) if g.target_amount else 0
            st.write(f"**{g.name}** — ₹{g.current_amount:,.0f} / ₹{g.target_amount:,.0f}")
            st.progress(progress)

            pacing = get_goal_pacing(g)
            if pacing:
                if pacing["status"] == "overdue" and pacing["amount_remaining"] > 0:
                    st.error(f"Target date has passed — still ₹{pacing['amount_remaining']:,.0f} short")
                elif pacing["status"] == "active":
                    st.caption(f"Save ₹{pacing['required_weekly']:,.0f}/week for {pacing['days_remaining']} more days to hit this on time")

            col1, col2 = st.columns([3, 1])
            with col1:
                contribution = st.number_input(f"Add to {g.name}", min_value=0.0, step=100.0, key=f"contrib_{g.id}")
            with col2:
                st.write("")
                if st.button("Add", key=f"btn_{g.id}"):
                    add_contribution(g.id, contribution)
                    st.rerun()
    else:
        st.info("No goals yet — add one above.")

# ==================================================
# TAB: BUDGETS
# ==================================================
with tab_budgets:
    st.header("📅 Budgets")

    with st.expander("➕ Set / Update Budget"):
        with st.form("add_budget_form"):
            budget_category = st.selectbox("Category", EXPENSE_CATEGORIES)
            budget_amount = st.number_input("Monthly Budget (₹)", min_value=0.0, step=100.0)
            budget_submitted = st.form_submit_button("Save Budget")

    if budget_submitted:
        add_budget(budget_category, budget_amount, current_month)
        st.rerun()

    budgets = get_budgets_for_month(current_month)

    if budgets:
        for b in budgets:
            velocity = get_budget_velocity(b.category, current_month, b.amount)
            progress = min(velocity["spent"] / b.amount, 1.0) if b.amount else 0

            st.write(f"**{b.category}** — ₹{velocity['spent']:,.0f} / ₹{b.amount:,.0f}")
            st.progress(progress)

            if velocity["spent"] > b.amount:
                st.error(f"Over budget by ₹{velocity['spent'] - b.amount:,.0f}")
            elif velocity["will_exceed"]:
                st.warning(
                    f"At your current pace (₹{velocity['daily_rate']:,.0f}/day), "
                    f"you'll reach ₹{velocity['projected_month_end']:,.0f} by month end — over budget. "
                    f"Stay under ₹{velocity['safe_daily_spend']:,.0f}/day for the rest of the month to avoid this."
                )
            else:
                st.caption(
                    f"On track — ₹{b.amount - velocity['spent']:,.0f} remaining, "
                    f"₹{velocity['safe_daily_spend']:,.0f}/day available for {velocity['days_remaining']} more days"
                )
    else:
        st.info(f"No budgets set for {current_month} yet — add one above.")

# ==================================================
# TAB: UPCOMING & EXPECTED
# ==================================================
with tab_upcoming:
    st.header("🔮 Upcoming & Expected")

    with st.expander("➕ Add Expected Transaction"):
        exp_type = st.selectbox("Type", ["expense", "income"], key="expected_type")
        exp_categories = EXPENSE_CATEGORIES if exp_type == "expense" else INCOME_CATEGORIES

        with st.form("add_expected_form"):
            exp_label = st.text_input("Label", placeholder="e.g. Goa Trip, Netflix Renewal, Client Payment")
            exp_category = st.selectbox("Category", exp_categories)
            exp_amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            exp_date = st.date_input("Expected Date")
            exp_recurring = st.selectbox("Recurring?", ["no", "monthly", "weekly"])
            exp_submitted = st.form_submit_button("Add")

    if exp_submitted:
        add_expected_transaction(
            exp_label, exp_type, exp_category, exp_amount,
            datetime.combine(exp_date, datetime.min.time()), exp_recurring
        )
        st.success(f"✅ Added: {exp_label}")
        st.rerun()

    expected_items = get_all_expected()

    if expected_items:
        for item in expected_items:
            col1, col2 = st.columns([4, 1])
            with col1:
                days_away = (item.expected_date - datetime.now()).days
                when = f"in {days_away} days" if days_away >= 0 else f"{abs(days_away)} days ago"
                st.write(f"**{item.label}** — ₹{item.amount:,.0f} ({item.category}) — {when} — *{item.status}*")
            with col2:
                if item.status == "pending":
                    if st.button("Cancel", key=f"cancel_{item.id}"):
                        mark_status(item.id, "cancelled")
                        st.rerun()
    else:
        st.info("No expected transactions yet — add one above.")


# run using 
# streamlit run app/ui/main.py