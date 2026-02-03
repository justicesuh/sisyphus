from django.conf import settings
from openai import OpenAI as OpenAIClient


class OpenAI:
    def __init__(self):
        self.client = OpenAIClient(api_key=settings.OPENAI_API_KEY)

    def chat(self, messages, model='gpt-4o', temperature=0.7, max_tokens=None, **kwargs):
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.choices[0].message.content

    def complete(self, prompt, system=None, **kwargs):
        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})
        return self.chat(messages, **kwargs)
