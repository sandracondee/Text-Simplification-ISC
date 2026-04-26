import os
import importlib
from typing import Optional


def _is_local_mode_enabled() -> bool:
    return os.getenv("LOCAL_MODE", "").strip().lower() in {"1", "true", "yes", "on"}


def _resolve_provider() -> str:
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider:
        return provider
    return "ollama" if _is_local_mode_enabled() else "gemini"


def build_chat_llm(temperature: float = 0.0, model: Optional[str] = None):
    provider = _resolve_provider()

    if provider == "ollama":
        try:
            chat_ollama_module = importlib.import_module("langchain_ollama")
            ChatOllama = getattr(chat_ollama_module, "ChatOllama")
        except ImportError as exc:
            raise ImportError(
                "`langchain-ollama` is required for Ollama mode. "
                "Install it with: pip install langchain-ollama"
            ) from exc

        model_name = model or os.getenv("OLLAMA_MODEL", "mistral")
        base_url = os.getenv("OLLAMA_BASE_URL", "").strip()

        kwargs = {
            "model": model_name,
            "temperature": temperature,
        }
        if base_url:
            kwargs["base_url"] = base_url

        return ChatOllama(**kwargs)

    if provider == "gemini":
        try:
            genai_module = importlib.import_module("langchain_google_genai")
            ChatGoogleGenerativeAI = getattr(genai_module, "ChatGoogleGenerativeAI")
        except ImportError as exc:
            raise ImportError(
                "`langchain-google-genai` is required for Gemini mode. "
                "Install it with: pip install langchain-google-genai"
            ) from exc

        model_name = model or os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)

    raise ValueError(
        f"Unsupported LLM_PROVIDER='{provider}'. Supported values: 'gemini' or 'ollama'."
    )
