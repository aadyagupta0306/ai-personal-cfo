# create_tables.py
from app.database.connection import engine
from app.models.transaction import Base
import app.models.budget

Base.metadata.create_all(engine)
print("Tables created successfully!")