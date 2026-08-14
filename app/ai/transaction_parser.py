import json
from datetime import datetime
from app.ai.client import call_llm
from app.constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES

from datetime import timedelta

def build_prompt(text, pending_items=None):
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    pending_items = pending_items or []

    pending_text = "\n".join(
        f"- id={p['id']}: \"{p['label']}\" ({p['type']}, {p['category']}, ₹{p['amount']}, expected {p['expected_date']})"
        for p in pending_items
    ) or "None"

    # "N days ago" lookup — for phrases like "3 days back"
    days_ago_table = "\n".join(
        f"{i} days ago = {(today - timedelta(days=i)).strftime('%Y-%m-%d')}"
        for i in range(1, 11)
    )

    # exactly one entry per weekday name — the MOST RECENT past occurrence, no duplicates
    weekday_table_lines = []
    seen_weekdays = set()
    for i in range(1, 8):
        candidate = today - timedelta(days=i)
        wd = candidate.strftime("%A")
        if wd not in seen_weekdays:
            weekday_table_lines.append(f"last {wd} = {candidate.strftime('%Y-%m-%d')}")
            seen_weekdays.add(wd)
    weekday_table = "\n".join(weekday_table_lines)

    return f"""You are a financial transaction parser. Convert the user's message into a single JSON object with these exact fields:
- amount (number)
- type ("income" or "expense")
- category (must be exactly one value from the lists below, matching type)
- description (short string, or null)
- date (format YYYY-MM-DD)
- matched_expected_id (integer id from the pending list below if this message clearly refers to one of them, otherwise null)

Expense categories: {EXPENSE_CATEGORIES}
Income categories: {INCOME_CATEGORIES}

Pending expected transactions (the user may be confirming one of these happened):
{pending_text}

Today's date is {today_str} ({today.strftime('%A')}).

For phrases like "N days ago" or "N days back", use this table:
{days_ago_table}

For phrases like "last Monday", "last Tuesday", etc., use this table (each is the single most recent past occurrence — do not pick an earlier date even if one exists further back):
{weekday_table}

If the user's message refers to one of the pending items above (by name or clear description) and does not explicitly state a different amount, still extract amount/date as best guess from the message — matched_expected_id is what matters, we'll use our own records for the final values.

Do not correct, adjust, or interpret invalid values. If the amount in the message is negative or zero, output it exactly as stated — do not change its sign or value. Extract exactly what the user wrote, even if it seems wrong.

Respond with ONLY the JSON object. No explanation, no markdown formatting.

User message: "{text}"
"""

def parse_transaction(text, pending_items=None):
    prompt = build_prompt(text, pending_items)
    raw_response = call_llm(prompt, temperature=0)
    cleaned = raw_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)

from app.constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES

def validate_parsed(data):
    errors = []

    if not isinstance(data.get("amount"), (int, float)) or data["amount"] <= 0:
        errors.append("Invalid amount")

    if data.get("type") not in ("income", "expense"):
        errors.append("Invalid type")

    valid_categories = EXPENSE_CATEGORIES if data.get("type") == "expense" else INCOME_CATEGORIES
    if data.get("category") not in valid_categories:
        errors.append(f"Category '{data.get('category')}' not recognized")

    try:
        datetime.strptime(data.get("date", ""), "%Y-%m-%d")
    except ValueError:
        errors.append("Invalid date format")

    return errors