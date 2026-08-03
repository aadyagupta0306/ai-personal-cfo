from app.database.session import SessionLocal
from app.models.chat_message import ChatMessage

def save_message(role, content):
    session = SessionLocal()
    try:
        msg = ChatMessage(role=role, content=content)
        session.add(msg)
        session.commit()
    finally:
        session.close()

def get_recent_history(limit=20):
    session = SessionLocal()
    try:
        messages = session.query(ChatMessage).order_by(ChatMessage.created_at.desc()).limit(limit).all()
        messages.reverse()  # oldest first, for correct conversation order
        return [{"role": m.role, "content": m.content} for m in messages]
    finally:
        session.close()

from app.models.chat_summary import ChatSummary
from app.ai.client import call_llm

SUMMARY_TRIGGER_COUNT = 20   # summarize once this many un-summarized messages pile up
KEEP_RAW_RECENT = 10          # always keep this many most recent messages verbatim

def get_or_create_summary():
    session = SessionLocal()
    try:
        summary = session.query(ChatSummary).first()
        if not summary:
            summary = ChatSummary(summary_text="", last_summarized_message_id=0)
            session.add(summary)
            session.commit()
            session.refresh(summary)
        return summary
    finally:
        session.close()

def maybe_update_summary():
    session = SessionLocal()
    try:
        summary_row = session.query(ChatSummary).first()
        last_id = summary_row.last_summarized_message_id if summary_row else 0

        unsummarized = session.query(ChatMessage).filter(
            ChatMessage.id > last_id
        ).order_by(ChatMessage.id).all()

        # leave the most recent KEEP_RAW_RECENT untouched, only summarize older overflow
        to_summarize = unsummarized[:-KEEP_RAW_RECENT] if len(unsummarized) > SUMMARY_TRIGGER_COUNT else []

        if not to_summarize:
            return

        convo_text = "\n".join(f"{m.role}: {m.content}" for m in to_summarize)
        prompt = f"""Summarize the key facts, decisions, and context from this financial conversation in a few concise sentences. Focus on what would be useful to remember later (goals discussed, advice given, concerns raised). Do not include pleasantries.

Previous summary (if any): {summary_row.summary_text if summary_row else ''}

New messages to incorporate:
{convo_text}

Write the updated combined summary:"""

        new_summary = call_llm(prompt, temperature=0.3)

        if not summary_row:
            summary_row = ChatSummary()
            session.add(summary_row)

        summary_row.summary_text = new_summary
        summary_row.last_summarized_message_id = to_summarize[-1].id
        session.commit()
    finally:
        session.close()

def get_context_for_chat():
    summary = get_or_create_summary()
    recent = get_recent_history(KEEP_RAW_RECENT)
    return summary.summary_text, recent