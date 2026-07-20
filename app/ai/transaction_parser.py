import json
from datetime import datetime
from app.ai.client import call_llm
from app.constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES

def build_prompt(text):
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""You are a financial transaction parser. Convert the user's message into a single JSON object with these exact fields:
- amount (number)
- type ("income" or "expense")
- category (must be exactly one value from the lists below, matching type)
- description (short string, or null)
- date (format YYYY-MM-DD)

Expense categories: {EXPENSE_CATEGORIES}
Income categories: {INCOME_CATEGORIES}

Today's date is {today}. Resolve relative dates like "yesterday" or "last Monday" based on this.
Do not correct, adjust, or interpret invalid values. If the amount in the message is negative or zero, output it exactly as stated — do not change its sign or value. 
Extract exactly what the user wrote, even if it seems wrong.
Respond with ONLY the JSON object. No explanation, no markdown formatting.

User message: "{text}"
"""

def parse_transaction(text):
    prompt = build_prompt(text)
    raw_response = call_llm(prompt)
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