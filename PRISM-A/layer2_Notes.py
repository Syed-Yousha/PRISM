# layer2_Notes.py

"""
PRISM – Layer 2: Notes Generator
--------------------------------
This layer reads the detailed explanation from Layer 1 (layer1_output.txt)
and converts it into concise, brainstorming-style whiteboard notes.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from prompts import notes_prompt

# Load API Key from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_notes(answer_text: str):
    """
    Takes the detailed Layer 1 answer and generates whiteboard-style notes.
    """
    prompt = notes_prompt(answer_text)

    response = client.chat.completions.create(
        model="gpt-5-mini",  # or use snapshot e.g. "gpt-5-mini-2025-08-07"
        messages=[
            {"role": "system", "content": "You are PRISM, a helpful AI note-maker."},
            {"role": "user", "content": prompt}
        ]
    )

    # Extract and return GPT response
    return response.choices[0].message.content


if __name__ == "__main__":
    # ✅ Step 1: Load Layer 1 output (from layer1_QA.py)
    try:
        with open("layer1_output.txt", "r", encoding="utf-8") as f:
            answer_text = f.read().strip()
    except FileNotFoundError:
        print("⚠️ Error: layer1_output.txt not found. Run layer1_QA.py first!")
        exit()

    # ✅ Step 2: Generate whiteboard-style notes
    notes = generate_notes(answer_text)

    # ✅ Step 3: Display notes on console
    print("\n--- PRISM's Notes (Layer 2) ---\n")
    print(notes)

    # ✅ Step 4: Save output to file (for next layer – e.g., visualization or text-to-video)
    with open("layer2_notes.txt", "w", encoding="utf-8") as f:
        f.write(notes)

    print("\n✅ Notes saved to layer2_notes.txt")
