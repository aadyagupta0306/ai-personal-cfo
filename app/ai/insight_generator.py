from app.ai.client import call_llm

def build_insight_facts(comparison_df, budgets_status):
    facts = []

    for _, row in comparison_df.iterrows():
        if row["change_pct"] >= 30 and row["this_month"] > 0:
            facts.append(f"{row['category']} spending changed from ₹{row['last_month']:.0f} to ₹{row['this_month']:.0f} ({row['change_pct']:.0f}% change)")

    for b in budgets_status:
        if b["spent"] > b["budget"]:
            facts.append(f"{b['category']} is over budget: spent ₹{b['spent']:.0f} against a ₹{b['budget']:.0f} limit")

    return facts

def generate_insights(facts):
    if not facts:
        return "No significant changes or budget concerns this month — spending looks steady."

    facts_text = "\n".join(f"- {f}" for f in facts)
    prompt = f"""You are a financial assistant. Below are factual observations about the user's spending, already calculated. Do not invent numbers or add facts not listed.

Facts:
{facts_text}

Write 2-3 short, direct sentences highlighting the most important patterns. Prioritize budget overruns over general increases. Do not use markdown.
"""
    return call_llm(prompt)