import requests

from config.settings import settings


def generate(prompt: str) -> str:
    """Send prompt to Ollama and return generated text."""

    try:

        response = requests.post(
            f"{settings.ollama_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=300,
        )

        response.raise_for_status()

        return response.json()["response"]

    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            "❌ Ollama is not running.\n\nRun:\n\nollama serve"
        )

    except Exception as e:

        raise RuntimeError(
            f"Ollama error:\n{e}"
        )