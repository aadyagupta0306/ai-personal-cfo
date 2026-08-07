from datetime import datetime
from app.database.session import SessionLocal
from app.models.daily_briefing import DailyBriefing
from app.ai.client import call_llm

def get_or_generate_briefing(alerts, force_refresh=False):
    today_str = datetime.now().strftime("%Y-%m-%d")
    session = SessionLocal()
    try:
        existing = session.query(DailyBriefing).filter(DailyBriefing.generated_date == today_str).first()

        if existing and not force_refresh:
            return existing.briefing_text

        if not alerts:
            text = "Nothing urgent today — your finances look steady. No budget overruns, goals on track, no red flags in the next 7 days."
        else:
            alerts_text = "\n".join(f"- {a}" for a in alerts)
            prompt = f"""You are a personal CFO giving a short daily briefing. Below are factual, pre-calculated financial alerts. Do not invent numbers or facts not listed.

Alerts:
{alerts_text}

Write a brief, direct 2-4 sentence briefing. Prioritize the most urgent/actionable items first. Tone: calm, helpful, not alarmist.
"""
            text = call_llm(prompt, temperature=0.3)

        if existing:
            existing.briefing_text = text
        else:
            session.add(DailyBriefing(briefing_text=text, generated_date=today_str))

        session.commit()
        return text
    finally:
        session.close()