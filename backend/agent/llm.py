from backend.config import get_settings
from backend.logging_setup import get_logger

logger = get_logger("llm")

_DEFAULT_MODEL = "gemini-2.5-flash"


def get_gemini_model_name() -> str:
    return get_settings().gemini_model or _DEFAULT_MODEL


def build_chat_model(api_key: str | None = None):
    from langchain_google_genai import ChatGoogleGenerativeAI

    settings = get_settings()
    key = api_key if api_key is not None else settings.gemini_api_key
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    return ChatGoogleGenerativeAI(
        model=get_gemini_model_name(),
        google_api_key=key,
        temperature=0.2,
    )
