from ai.provider import ask_json


def generate_characters(title, genre, theme):
    prompt = f"""
Create 3 movie characters.

Return ONLY valid JSON. No markdown. No explanation.

[
  {{
    "name": "",
    "age": "",
    "role": "",
    "personality": "",
    "goal": "",
    "conflict": ""
  }}
]

Movie:
Title: {title}
Genre: {genre}
Theme: {theme}
"""

    return ask_json(prompt)