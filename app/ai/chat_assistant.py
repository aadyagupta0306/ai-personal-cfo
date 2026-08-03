from app.ai.client import call_llm
from app.ai.context_builder import build_financial_context

SYSTEM_INSTRUCTIONS = """You are a personal CFO assistant. You have been given the user's real, current financial data below.

Rules you must follow:
- Only use the numbers provided in the CONTEXT section. Never invent, estimate, or assume numbers not present there.
- If the context doesn't contain enough information to answer confidently, say so clearly instead of guessing.
- Give direct, practical, specific advice — not generic financial tips.
- Reference actual goal names, categories, and amounts from the context when relevant.
- You cannot take any action (you cannot add, edit, or delete anything) — you can only inform and advise.
- Keep responses concise and conversational, not a report.
"""

def chat_with_cfo(user_message, summary_text, recent_history):
    context = build_financial_context()

    full_prompt_parts = [SYSTEM_INSTRUCTIONS, "\nCONTEXT (current financial data):\n" + context]

    if summary_text:
        full_prompt_parts.append("\nSUMMARY OF EARLIER CONVERSATION:\n" + summary_text)

    full_prompt_parts.append("\nRECENT CONVERSATION:")
    for turn in recent_history:
        role = "User" if turn["role"] == "user" else "Assistant"
        full_prompt_parts.append(f"{role}: {turn['content']}")

    full_prompt_parts.append(f"User: {user_message}")
    full_prompt_parts.append("Assistant:")

    return call_llm("\n".join(full_prompt_parts), temperature=0.4)