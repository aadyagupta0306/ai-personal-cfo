import requests
from config import OPENROUTER_API_KEY

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-oss-20b:free"

def call_llm(prompt, temperature=0.7):
    response = requests.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        },
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]