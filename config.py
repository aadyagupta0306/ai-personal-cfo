import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

def get_secret(key):
    value = os.getenv(key)
    if value:
        return value
    try:
        return st.secrets[key]
    except Exception:
        return None

DATABASE_URL = get_secret("DATABASE_URL")
OPENROUTER_API_KEY = get_secret("OPENROUTER_API_KEY")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL not found. Check your .env file or Streamlit secrets.")
if OPENROUTER_API_KEY is None:
    raise ValueError("OPENROUTER_API_KEY not found. Check your .env file or Streamlit secrets.")