def slug(text: str) -> str:
    return text.lower().replace(" ", "_").replace("-", "_")