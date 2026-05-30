import os
from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistralAI


def get_llm(provider: str = "anthropic"):
    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY is not set.")
        return ChatAnthropic(
            model="claude-sonnet-4-6",
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
