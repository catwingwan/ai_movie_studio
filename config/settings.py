from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:

    # AI Provider
    ai_provider: str = os.getenv("AI_PROVIDER", "ollama")

    # Ollama
    ollama_url: str = os.getenv(
        "OLLAMA_URL",
        "http://localhost:11434"
    )

    ollama_model: str = os.getenv(
        "OLLAMA_MODEL",
        "llama3.2:3b"
    )

    # OpenAI (future-proofing)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Project storage
    data_dir: str = os.getenv("DATA_DIR", "data/projects")


settings = Settings()