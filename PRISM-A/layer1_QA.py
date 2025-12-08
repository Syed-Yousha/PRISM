# layer1_QA.py
"""
PRISM – Layer 1: Question–Answer Generator
------------------------------------------
This layer takes a student's query and produces a detailed,
teacher-style explanation using the GPT model.
The output is saved to layer1_output.txt for Layer 2 (notes generator).
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from prompts import generated_prompt   # from prompts.py

# Load API key from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def ask_prism(query: str) -> str:
    """
    Sends the user's question to GPT and returns the AI's detailed answer.
    """
    prompt = generated_prompt(query)

    response = client.chat.completions.create(
        model="gpt-5-mini",   # or snapshot e.g. "gpt-5-mini-2025-08-07"
        messages=[
            {"role": "system", "content": "You are PRISM, a friendly AI tutor."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    print("🎓 Welcome to PRISM (Layer 1 – Q&A Engine)\n")
    user_query = input("Enter your question or topic: ").strip()

    if not user_query:
        print("⚠️ Please enter a valid question.")
        exit()

    print("\n⏳ Generating explanation...\n")
    answer = ask_prism(user_query)

    print("\n--- PRISM's Answer ---\n")
    print(answer)

    # Save Layer 1 output for Layer 2
    with open("layer1_output.txt", "w", encoding="utf-8") as f:
        f.write(answer)

    print("\n✅ Saved detailed answer to layer1_output.txt")

