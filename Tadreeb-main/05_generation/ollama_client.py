"""
LLM access: a local Ollama model, or a hosted API, chosen by `LLM_PROVIDER`.

    LLM_PROVIDER=ollama   (default)  the local fine-tuned Qwen, as before
    LLM_PROVIDER=groq                Groq - fast, free tier, good Arabic
    LLM_PROVIDER=openai              OpenAI
    LLM_PROVIDER=gemini              Google Gemini
    LLM_PROVIDER=api                 any other OpenAI-compatible endpoint (LLM_API_URL)

    LLM_API_KEY=...        the key for whichever hosted provider is selected
    LLM_MODEL=...          its model id (each provider has a sensible default)

Groq and OpenAI speak the same chat-completions shape, so they share one code
path; Gemini needs its own request body. That is the whole "abstraction" - a URL,
a header and a response path per provider, with no registry or plugin layer.

**Ollama always stays available as the fallback.** If a hosted call fails for any
reason - no key, rate limit, network - the prompt is retried locally rather than
failing the request, so the chatbot keeps working with no internet access.

A second, optional setting lets the *query-understanding* step use a different
(faster, cheaper) provider from the one that writes the answer:

    QUERY_LLM_PROVIDER=groq          defaults to LLM_PROVIDER when unset
    QUERY_LLM_MODEL=...

Keys are only ever read from the environment / `.env`; none are hardcoded.
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

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

LLM_API_URL = os.getenv("LLM_API_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")

# The query-understanding step may use a different provider from the answer step;
# unset means "the same one".
QUERY_LLM_PROVIDER = os.getenv("QUERY_LLM_PROVIDER", "").strip().lower() or LLM_PROVIDER
QUERY_LLM_MODEL = os.getenv("QUERY_LLM_MODEL", "")

# url + default model per hosted provider. Groq and OpenAI are both
# OpenAI-compatible; Gemini differs only in the request/response shape.
HOSTED_PROVIDERS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile",
        "shape": "openai",
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini",
        "shape": "openai",
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "model": "gemini-2.0-flash",
        "shape": "gemini",
    },
}
HOSTED_TIMEOUT = int(os.getenv("LLM_API_TIMEOUT", "60"))

# A grounded prompt carries five labelled source blocks plus instructions and
# recent turns. At the previous 2048 it did not fit, and Ollama drops the
# *front* of an oversized prompt - which is where the "use only these sources"
# instructions live. The model then answered unconstrained. Keep this large
# enough that the whole prompt survives.
NUM_CTX = int(os.getenv("LLM_NUM_CTX", "8192"))
NUM_PREDICT = int(os.getenv("LLM_NUM_PREDICT", os.getenv("MAX_ANSWER_TOKENS", "180")))
# Low temperature: this is a factual lookup task, not a creative one.
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.15"))
REPEAT_PENALTY = float(os.getenv("LLM_REPEAT_PENALTY", "1.15"))
REPEAT_LAST_N = int(os.getenv("LLM_REPEAT_LAST_N", "128"))

# Rough characters-per-token for mixed Arabic/English; only used to warn when a
# prompt is about to be silently truncated.
_CHARS_PER_TOKEN = 2.5


def _options() -> dict:
    return {
        "num_predict": NUM_PREDICT,
        "num_ctx": NUM_CTX,
        "temperature": TEMPERATURE,
        "top_p": 0.9,
        "repeat_penalty": REPEAT_PENALTY,
        "repeat_last_n": REPEAT_LAST_N,
    }


def _warn_if_oversized(prompt: str) -> None:
    estimated = len(prompt) / _CHARS_PER_TOKEN
    if estimated > NUM_CTX * 0.9:
        print(
            f"Warning: prompt is ~{estimated:.0f} tokens against a {NUM_CTX}-token window. "
            "Raise LLM_NUM_CTX or reduce RETRIEVAL top_k - grounding instructions may be cut.",
            flush=True,
        )


def ask_ollama(prompt: str, model: str = FINETUNED_MODEL_NAME) -> str:
    """Send a prompt to Ollama, falling back to the base model if the tag is missing."""
    _warn_if_oversized(prompt)
    try:
        response = ollama.generate(model=model, prompt=prompt, options=_options())
        return response["response"].strip()
    except Exception:
        # Fallback to base model if the custom model tag isn't available
        if model != BASE_MODEL:
            response = ollama.generate(model=BASE_MODEL, prompt=prompt, options=_options())
            return response["response"].strip()
        raise


def ask_llm_api(prompt: str, url: str = "", model: str = "") -> str:
    """Send a prompt to a custom OpenAI-compatible LLM API (`LLM_PROVIDER=api`)."""
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
    }
    if model:
        payload["model"] = model
    response = requests.post(
        url or LLM_API_URL,
        headers={"Authorization": f"Bearer {LLM_API_KEY}"},
        json=payload,
        timeout=HOSTED_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def ask_hosted(prompt: str, provider: str, model: str = "") -> str:
    """One call to a named hosted provider. Raises on failure; the caller falls back."""
    config = HOSTED_PROVIDERS[provider]
    model = model or config["model"]
    if not LLM_API_KEY:
        raise RuntimeError(f"LLM_PROVIDER={provider} needs LLM_API_KEY to be set")

    if config["shape"] == "gemini":
        response = requests.post(
            config["url"].format(model=model),
            headers={"x-goog-api-key": LLM_API_KEY, "Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": TEMPERATURE,
                                     "maxOutputTokens": NUM_PREDICT},
            },
            timeout=HOSTED_TIMEOUT,
        )
        response.raise_for_status()
        parts = response.json()["candidates"][0]["content"]["parts"]
        return "".join(part.get("text", "") for part in parts).strip()

    response = requests.post(
        config["url"],
        headers={"Authorization": f"Bearer {LLM_API_KEY}",
                 "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": TEMPERATURE,
            "max_tokens": NUM_PREDICT,
        },
        timeout=HOSTED_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def ask_model(prompt: str, purpose: str = "answer") -> str:
    """Send a prompt to the configured provider, falling back to local Ollama.

    `purpose="query"` uses QUERY_LLM_PROVIDER / QUERY_LLM_MODEL when they are set,
    so the cheap, fast query-rewriting step can run on a hosted model while the
    grounded answer is still written by the local fine-tuned Qwen (or the reverse).
    """
    provider = QUERY_LLM_PROVIDER if purpose == "query" else LLM_PROVIDER
    model = QUERY_LLM_MODEL if purpose == "query" else LLM_MODEL

    if provider in HOSTED_PROVIDERS:
        try:
            return ask_hosted(prompt, provider, model)
        except Exception as e:
            print(f"Warning: {provider} call failed ({e}); falling back to local Ollama.",
                  flush=True)
    elif provider == "api" and LLM_API_URL:
        try:
            return ask_llm_api(prompt, model=model)
        except Exception as e:
            print(f"Warning: external API call failed ({e}); falling back to local Ollama.",
                  flush=True)

    return ask_ollama(prompt)
