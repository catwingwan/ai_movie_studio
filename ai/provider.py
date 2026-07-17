from ai.ollama import generate
from ai.parser import parse_json


def ask(prompt: str) -> str:
    return generate(prompt)


def ask_json(prompt: str):
    response = ask(prompt)
    return parse_json(response)