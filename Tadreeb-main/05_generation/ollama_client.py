"""
Handles LLM generation via local Ollama (fine-tuned or base model), with an
optional generic external OpenAI-compatible API as a configurable alternative.
"""
import os
from pathlib import Path
import ollama
import requests

# Load root .env
try:
    from dotenv import load_dotenv
    root_env = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(root_env)
except Exception:
    pass

BASE_MODEL = os.getenv("BASE_MODEL", "llama3.2:latest")
FINETUNED_MODEL_NAME = os.getenv("FINETUNED_MODEL_NAME", "depi-iti-nti-assistant")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()  # "ollama" or "api"

LLM_API_URL = os.getenv("LLM_API_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")


def ask_ollama(prompt: str, model: str = FINETUNED_MODEL_NAME) -> str:
    """Send a prompt to Ollama with speed optimizations for CPU and fallback."""
    options = {
        "num_predict": 300,   # Limit max tokens to speed up CPU response
        "num_ctx": 2048,      # Reduced context window for faster processing
        "temperature": 0.3,
        "top_p": 0.9,
    }
    try:
        response = ollama.generate(model=model, prompt=prompt, options=options)
        return response["response"].strip()
    except Exception:
        # Fallback to base model if the custom model tag isn't available
        if model != BASE_MODEL:
            response = ollama.generate(model=BASE_MODEL, prompt=prompt, options=options)
            return response["response"].strip()
        raise


def ask_llm_api(prompt: str) -> str:
    """Send a prompt to an external OpenAI-compatible LLM API."""
    response = requests.post(
        LLM_API_URL,
        headers={"Authorization": f"Bearer {LLM_API_KEY}"},
        json={"messages": [{"role": "user", "content": prompt}]},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def ask_model(prompt: str) -> str:
    """Route prompt to the configured provider: generic external API, or local Ollama (default)."""
    if LLM_PROVIDER == "api" and LLM_API_URL:
        try:
            return ask_llm_api(prompt)
        except Exception as e:
            print(f"Warning: External API call failed ({e}), falling back to local Ollama...")

    return ask_ollama(prompt)
