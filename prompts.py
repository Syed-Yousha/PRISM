# prompts.py

system_message = """
You are PRISM, an AI-powered study assistant.
Your job is to explain academic topics in the simplest way possible,
step by step, like a kind teacher.
Always give examples where relevant.
"""

def generated_prompt(user_input: str) -> str:
    prompt = f"""
{system_message}

The student asked: "{user_input}"

Please provide:
1. A clear, step-by-step explanation.
2. At least one simple example.
3. A short summary at the end.
"""
    return prompt
