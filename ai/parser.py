import json
import re


class AIParseError(Exception):
    """Raised when AI output cannot be parsed."""
    pass


def clean_response(text: str) -> str:
    """Remove markdown code fences and whitespace."""

    text = text.strip()

    # Remove ```json
    text = re.sub(r"^```(?:json)?", "", text)

    # Remove ```
    text = re.sub(r"```$", "", text)

    return text.strip()

def parse_json(text: str):

    cleaned = clean_response(text)

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError as exc:

        raise AIParseError(
            f"Invalid JSON returned by AI:\n\n{cleaned}"
        ) from exc