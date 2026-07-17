from dotenv import load_dotenv
import os

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama")

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen3:8b"
)

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
)