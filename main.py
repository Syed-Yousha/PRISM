import os
from openai import OpenAI
from dotenv import load_dotenv
from prompts import generated_prompt

# Load API key from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_prism(query: str):
    prompt = generated_prompt(query)

    response = client.chat.completions.create(
        model="gpt-5-mini",   # ya snapshot model e.g. "gpt-5-mini-2025-08-07"
        messages=[
            {"role": "system", "content": "You are PRISM, a helpful AI tutor."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    user_query = input("Enter your question: ")
    answer = ask_prism(user_query)
    print("\n--- PRISM's Answer ---\n")
    print(answer)
