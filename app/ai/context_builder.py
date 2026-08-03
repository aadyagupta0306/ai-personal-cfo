from datetime import datetime
from app.services.account_service import get_all_accounts, get_account_balance
from app.services.goal_service import get_all_goals, get_goal_pacing
from app.services.budget_service import get_budgets_for_month, get_budget_velocity
from app.services.expected_transaction_service import get_forecast
from app.services.analytics_service import get_transactions_df, get_summary, get_category_breakdown

def build_financial_context():
    current_month = datetime.now().strftime("%Y-%m")
    lines = []

    # Accounts
    accounts = get_all_accounts()
    lines.append("ACCOUNTS:")
    total_balance = 0
    for a in accounts:
        bal = get_account_balance(a.id)
        total_balance += bal
        lines.append(f"- {a.name} ({a.account_type}): ₹{bal:,.0f}")
    lines.append(f"Total across all accounts: ₹{total_balance:,.0f}")

    # This month's income/expense
    df = get_transactions_df()
    if not df.empty:
        income, expense, savings = get_summary(df)
        lines.append(f"\nALL-TIME TOTALS: Income ₹{income:,.0f}, Expense ₹{expense:,.0f}, Net Savings ₹{savings:,.0f}")

        breakdown = get_category_breakdown(df, "expense")
        if not breakdown.empty:
            lines.append("\nEXPENSE BREAKDOWN BY CATEGORY (all-time):")
            for _, row in breakdown.iterrows():
                lines.append(f"- {row['category']}: ₹{row['amount']:,.0f}")

    # Goals
    goals = get_all_goals()
    if goals:
        lines.append("\nGOALS:")
        for g in goals:
            pacing = get_goal_pacing(g)
            line = f"- {g.name}: ₹{g.current_amount:,.0f} / ₹{g.target_amount:,.0f} saved"
            if pacing and pacing.get("status") == "active":
                line += f" (need ₹{pacing['required_weekly']:,.0f}/week, {pacing['days_remaining']} days left)"
            elif pacing and pacing.get("status") == "overdue":
                line += " (target date has passed, still short)"
            lines.append(line)

    # Budgets
    budgets = get_budgets_for_month(current_month)
    if budgets:
        lines.append("\nBUDGETS THIS MONTH:")
        for b in budgets:
            v = get_budget_velocity(b.category, current_month, b.amount)
            status = "OVER BUDGET" if v["spent"] > b.amount else ("ON PACE TO EXCEED" if v["will_exceed"] else "on track")
            lines.append(f"- {b.category}: ₹{v['spent']:,.0f} / ₹{b.amount:,.0f} spent ({status}, safe to spend ₹{v['safe_daily_spend']:,.0f}/day for rest of month)")

    # Upcoming/expected
    forecast = get_forecast(60)
    if forecast:
        lines.append("\nUPCOMING (next 60 days):")
        for item in forecast:
            sign = "+" if item["type"] == "income" else "-"
            lines.append(f"- {item['date'].strftime('%b %d')}: {item['label']} ({sign}₹{item['amount']:,.0f})")

    return "\n".join(lines)