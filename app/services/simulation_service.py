from datetime import datetime

def simulate_scenario(hypothetical_events, total_balance, forecast_items, goals):
    events = list(forecast_items) + hypothetical_events
    events_sorted = sorted(events, key=lambda x: x["date"])

    running = total_balance
    lowest = total_balance
    lowest_date = datetime.now()
    timeline = [{"date": datetime.now(), "balance": running}]

    for ev in events_sorted:
        running += ev["amount"] if ev["type"] == "income" else -ev["amount"]
        timeline.append({"date": ev["date"], "balance": running})
        if running < lowest:
            lowest = running
            lowest_date = ev["date"]

    goal_warnings = []
    for g in goals:
        if g.goal_type == "emergency_fund" and lowest < g.target_amount:
            goal_warnings.append(
                f"{g.name} would dip below its ₹{g.target_amount:,.0f} target (lowest projected balance: ₹{lowest:,.0f})"
            )

    return {
        "timeline": timeline,
        "lowest_balance": lowest,
        "lowest_date": lowest_date,
        "goes_negative": lowest < 0,
        "goal_warnings": goal_warnings,
        "final_balance": running,
    }