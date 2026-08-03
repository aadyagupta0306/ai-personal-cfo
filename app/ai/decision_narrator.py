from app.ai.client import call_llm

def explain_scenario(facts, question_text):
    prompt = f"""You are a financial decision assistant. Below are deterministic facts already calculated from the user's real data about a hypothetical scenario. Do not invent or recalculate any numbers — only use what's given.

Final projected balance: ₹{facts['final_balance']:.0f}
Lowest projected balance: ₹{facts['lowest_balance']:.0f} on {facts['lowest_date'].strftime('%b %d')}
Goes negative at any point: {facts['goes_negative']}
Goal concerns: {facts['goal_warnings'] or 'None'}

User's question: "{question_text}"

Answer directly in 2-4 sentences, referencing these numbers specifically. Be clear about whether this seems advisable given the facts, not vague.
"""
    return call_llm(prompt, temperature=0.3)