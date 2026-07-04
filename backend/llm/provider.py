"""
LLM provider — tries Groq first, falls back to OpenRouter.
All agents call through `chat()` or `get_client()`.
"""

from openai import OpenAI, APIError, APITimeoutError

from backend.config import settings

# Models available on Groq (subset we use)
_GROQ_MODELS = {
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "whisper-large-v3",
}

# OpenRouter model IDs for models not on Groq
_OPENROUTER_ALIAS = {
    "google/gemini-2.5-flash": "google/gemini-2.5-flash",
}

_groq_client = OpenAI(
    api_key=settings.groq_api_key,
    base_url=settings.groq_base_url,
)

_or_client = OpenAI(
    api_key=settings.openrouter_api_key,
    base_url=settings.openrouter_base_url,
)


def get_client(model: str) -> tuple[OpenAI, str]:
    """Return (client, resolved_model_id) for the given model name."""
    if model in _GROQ_MODELS:
        return _groq_client, model
    if model in _OPENROUTER_ALIAS:
        return _or_client, _OPENROUTER_ALIAS[model]
    # Default: try Groq, it will error if unsupported
    return _groq_client, model


def chat(model: str, messages: list[dict], temperature: float = 0.2, **kwargs) -> str:
    """
    Send a chat completion request.
    Tries Groq first; falls back to OpenRouter on any API/timeout error.
    Returns the assistant message content string.
    """
    client, resolved_model = get_client(model)
    try:
        response = client.chat.completions.create(
            model=resolved_model,
            messages=messages,
            temperature=temperature,
            **kwargs,
        )
        return response.choices[0].message.content
    except (APIError, APITimeoutError, Exception):
        # Fallback to OpenRouter with the same model name
        fallback_model = _OPENROUTER_ALIAS.get(model, model)
        response = _or_client.chat.completions.create(
            model=fallback_model,
            messages=messages,
            temperature=temperature,
            **kwargs,
        )
        return response.choices[0].message.content
