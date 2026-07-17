"""Local AI generation and tolerant JSON parsing for character bibles."""

from __future__ import annotations

import json
import re
from typing import Any

from ai.provider import ask
from movie.character_bible_schema import CharacterBible

PROMPT = """You are creating a reusable visual character bible for a local open-source AI movie pipeline.

Return EXACTLY ONE valid JSON object and no Markdown.
Use concise visual details that can remain consistent across many generated images.
Do not name celebrities, copyrighted characters, brands, paid services, or cloud tools.
Do not infer sensitive identity attributes unless explicitly present in the source character.

Required keys:
name, role, age, gender_presentation, face, hair, eyes, skin_tone, body_type, height,
distinguishing_features, personality, default_wardrobe, color_palette,
consistency_prompt, negative_prompt, status

Rules:
- face, hair, eyes, skin_tone, body_type, height, consistency_prompt, and negative_prompt must each be a plain JSON string.
- distinguishing_features, default_wardrobe, and color_palette must be JSON arrays of strings.
- Do not return nested objects for any required field.
- consistency_prompt must be a single reusable visual description of the character.
- negative_prompt should prevent identity drift, duplicate people, malformed anatomy, text, logos, and watermarks.
- status must be "draft".

SOURCE CHARACTER JSON:
__CHARACTER_JSON__
"""


def _repair(text: str) -> str:
    stack: list[str] = []
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "{[":
            stack.append(char)
        elif char in "}]":
            if not stack:
                return text
            opening = stack.pop()
            if (opening, char) not in (("{", "}"), ("[", "]")):
                return text
    if in_string or escaped:
        return text
    closers = {"{": "}", "[": "]"}
    return text + "".join(closers[item] for item in reversed(stack))


def _repair_repeated_quotes(text: str) -> str:
    """Repair a common local-model error such as: "height":"5\'8""""."""
    return re.sub(
        r'(?<=\d)"{2,}(?=\s*[,}])',
        '\\\""',
        text,
    )



def _repair_missing_value_quotes(text: str) -> str:
    """Repair missing closing quotes before the next JSON key or container end.

    Local models sometimes emit values like::

        "face":"oval face,"hair":"brown"
        "wardrobe":["coat","shirt],"color_palette":[]

    The repair only acts while currently inside a JSON string and only when the
    following token is clearly another object key. It does not invent content.
    """
    result: list[str] = []
    in_string = False
    escaped = False
    index = 0
    length = len(text)

    def next_is_key(start: int) -> bool:
        return re.match(r'\s*,\s*"[^"\n]+"\s*:', text[start:]) is not None

    while index < length:
        char = text[index]

        if in_string:
            if escaped:
                result.append(char)
                escaped = False
                index += 1
                continue
            if char == "\\":
                result.append(char)
                escaped = True
                index += 1
                continue
            if char == '"':
                result.append(char)
                in_string = False
                index += 1
                continue

            # Missing quote immediately before a comma that starts the next key.
            if char == ',' and re.match(r'\s*"[^"\n]+"\s*:', text[index + 1:]):
                result.append('"')
                result.append(char)
                in_string = False
                index += 1
                continue

            # Missing quote before ] or } followed by the next object key.
            if char in ']}' and next_is_key(index + 1):
                result.append('"')
                result.append(char)
                in_string = False
                index += 1
                continue

            result.append(char)
            index += 1
            continue

        result.append(char)
        if char == '"':
            in_string = True
        index += 1

    return ''.join(result)

def parse_response(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        return response
    if not isinstance(response, str):
        raise ValueError("Character Bible AI returned an unsupported response type.")
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.strip(), flags=re.I)
    start = cleaned.find("{")
    if start < 0:
        raise ValueError(f"Invalid JSON returned by AI: {cleaned}")
    candidate = _repair_missing_value_quotes(_repair_repeated_quotes(cleaned[start:]))
    decoder = json.JSONDecoder()
    try:
        value, _ = decoder.raw_decode(candidate)
    except json.JSONDecodeError:
        repaired = _repair(candidate)
        try:
            value, _ = decoder.raw_decode(repaired)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON returned by AI: {cleaned}") from error
    if isinstance(value, dict) and isinstance(value.get("character"), dict):
        value = value["character"]
    if not isinstance(value, dict):
        raise ValueError("Character Bible AI did not return a JSON object.")
    return value


def generate_character_bible(character: dict[str, Any]) -> CharacterBible:
    prompt = PROMPT.replace(
        "__CHARACTER_JSON__",
        json.dumps(character, indent=2, ensure_ascii=False),
    )
    raw = ask(prompt)
    return CharacterBible.from_dict(parse_response(raw), character)
