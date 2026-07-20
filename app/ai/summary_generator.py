from app.ai.client import call_llm

def build_summary_prompt(period_label, income, expense, savings, category_breakdown):
    breakdown_text = "\n".join(f"- {row['category']}: ₹{row['amount']:.0f}" for _, row in category_breakdown.iterrows())

    return f"""You are a financial assistant writing a short, friendly summary for a {period_label}.
Use ONLY the numbers provided below — do not calculate or estimate anything yourself.

Income: ₹{income:.0f}
Expense: ₹{expense:.0f}
Net Savings: ₹{savings:.0f}

Expense breakdown by category:
{breakdown_text}

Write a 3-4 sentence summary in plain, encouraging language. Mention the biggest spending category by name. Do not use markdown formatting.
"""

def generate_summary(period_label, income, expense, savings, category_breakdown):
    prompt = build_summary_prompt(period_label, income, expense, savings, category_breakdown)
    return call_llm(prompt)