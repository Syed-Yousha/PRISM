# prompts.py

"""
PRISM Prompt Module
-------------------
This file defines prompt templates for:
1. Layer 1: Question-Answer Generation (Teacher-style explanation)
2. Layer 2: Notes Generation (Whiteboard-style brainstorming notes)
"""

# Base system message for PRISM
system_message = """
You are PRISM, an AI-powered study assistant.
Your personality is that of a calm, clear, and friendly teacher.
Always focus on simplifying complex topics and explaining them in an exam-oriented way.
"""

# -----------------------------------------------
# 🔹 LAYER 1: Teacher-Style Q&A Explanation Prompt
# -----------------------------------------------
def generated_prompt(user_input: str) -> str:
    """
    Takes the user's question and generates a detailed, teacher-style explanation prompt.
    """
    prompt = f"""
{system_message}

The student asked: "{user_input}"

Your task:
1. Explain the topic step-by-step like a teacher.
2. Use simple language and small sentences.
3. Give at least one easy example (numerical or conceptual).
4. End with a short summary of key points.

Output format:
### Explanation
[Step-by-step detailed answer]

### Example
[One relevant example]

### Summary
[3–4 line summary of the concept]
"""
    return prompt


# -----------------------------------------------
# 🔹 LAYER 2: Notes Conversion Prompt
# -----------------------------------------------
def notes_prompt(answer_text: str) -> str:
    """
    Converts a long teacher-style answer into structured, brainstorming-style notes
    for whiteboard display or video frames.
    """
    prompt = f"""
{system_message}

You are now in NOTES MODE.

Here is the detailed answer from Layer 1:
\"\"\"{answer_text}\"\"\"

Convert this into concise, frame-by-frame NOTES for a whiteboard presentation.
Keep the style simple, visual, and brainstorming-friendly.

Formatting instructions:
- Use bullet points, arrows (→), and symbols.
- Split information into clear "Frames" (Frame 1, Frame 2, Frame 3...).
- Avoid long sentences.
- Use simple formulas, keywords, and mini-summaries.
- Make it suitable for students taking quick notes.

Output format example:
### Frame 1 – Topic Introduction
- Definition / Concept
- Real-world meaning

### Frame 2 – Key Idea
- Important formula → Example usage

### Frame 3 – Summary
- Final takeaway points
"""
    return prompt
