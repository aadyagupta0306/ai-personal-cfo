# create_tables.py
from app.database.connection import engine
from app.models.transaction import Base
import app.models.chat_summary
import app.models.daily_briefing

Base.metadata.create_all(engine)
print("Tables created successfully!")