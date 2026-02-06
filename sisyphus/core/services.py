from functools import lru_cache
from typing import Any

from django.conf import settings
from openai import OpenAI as OpenAIClient


class OpenAI:
    """Wrapper around the OpenAI API client."""

    def __init__(self) -> None:
        self.client = OpenAIClient(api_key=settings.OPENAI_API_KEY)

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str = 'gpt-4o-mini',
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> str | None:
        """Send a chat completion request and return the response content."""
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            **kwargs,
        )
        return response.choices[0].message.content

    def complete(self, prompt: str, system: str | None = None, **kwargs: Any) -> str | None:
        """Send a single prompt completion request."""
        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})
        return self.chat(messages, **kwargs)


@lru_cache
def get_openai() -> OpenAI:
    """Return a cached OpenAI client instance."""
    return OpenAI()
