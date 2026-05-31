import os

import anthropic as _anthropic
from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistralAI

# Model constants — single source of truth for all modules
THINKING_MODEL = "claude-opus-4-8"   # extended thinking, highest reasoning quality
CACHING_MODEL  = "claude-sonnet-4-6" # prompt caching + tool use


def get_llm(provider: str = "anthropic"):
    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY is not set.")
        return ChatAnthropic(
            model=CACHING_MODEL,
            api_key=api_key,
            temperature=0.2,
            max_tokens=4096,
        )
    if provider == "mistral":
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            raise EnvironmentError("MISTRAL_API_KEY is not set.")
        return ChatMistralAI(
            model="mistral-large-latest",
            api_key=api_key,
            temperature=0.2,
        )
    raise ValueError(f"Unknown provider: {provider!r}. Choose 'anthropic' or 'mistral'.")


def get_native_client() -> _anthropic.Anthropic:
    """Native Anthropic client for prompt caching and extended thinking.

    Use this instead of get_llm() when you need:
    - cache_control on system messages (prompt caching)
    - thinking={...} (extended thinking / claude-opus-4-8)
    - tool_use with full content-block control
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not set.")
    return _anthropic.Anthropic(api_key=api_key)
