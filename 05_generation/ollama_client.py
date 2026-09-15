"""
Talks to the local Ollama server to generate the final answer with the
fine-tuned Qwen model (falls back to the base model if no fine-tuned model
has been created yet with 04_finetuning_pipeline/Modelfile).
"""
import os
import ollama
import requests

BASE_MODEL = os.getenv("BASE_MODEL", "qwen2.5:7b")
FINETUNED_MODEL_NAME = os.getenv("FINETUNED_MODEL_NAME", BASE_MODEL)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # "ollama" or "api"
LLM_API_URL = os.getenv("LLM_API_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")


def ask_ollama(prompt: str, model: str = FINETUNED_MODEL_NAME) -> str:
    """Send a prompt to Qwen through Ollama and return the answer text."""
    response = ollama.generate(model=model, prompt=prompt)
    return response["response"].strip()


def ask_llm_api(prompt: str) -> str:
    """Send a prompt to an external LLM API instead of a local Ollama model."""
    response = requests.post(
        LLM_API_URL,
        headers={"Authorization": f"Bearer {LLM_API_KEY}"},
        json={"messages": [{"role": "user", "content": prompt}]},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def ask_model(prompt: str) -> str:
    """Switch between the local fine-tuned Ollama model and an external LLM API."""
    if LLM_PROVIDER == "api":
        return ask_llm_api(prompt)
    return ask_ollama(prompt)
