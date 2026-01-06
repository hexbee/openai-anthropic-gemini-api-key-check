from typing import Optional, Generator

from openai import OpenAI

from .base import BaseProvider, ModelInfo


class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        super().__init__(api_key, base_url, system_prompt, default_model)
        self._client: Optional[OpenAI] = None

    @property
    def name(self) -> str:
        return "OpenAI"

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def list_models(self) -> list[ModelInfo]:
        """List all available models from OpenAI."""
        models = []
        for model in self.client.models.list():
            models.append(
                ModelInfo(
                    id=model.id,
                    name=model.id,
                    created=model.created,
                )
            )
        return models

    def validate_key(self) -> bool:
        """Validate the API key by attempting to list models."""
        try:
            self.list_models()
            return True
        except Exception:
            return False

    def chat(
        self,
        message: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        stream: bool = True,
    ) -> Generator[str, None, str]:
        """
        Send a chat message and get response (with streaming support).
        """
        model = model or self.default_model
        if not model:
            raise ValueError("No model specified and no default model set")

        # Build messages
        messages = []
        if system_prompt or self.system_prompt:
            messages.append({"role": "system", "content": system_prompt or self.system_prompt})
        messages.append({"role": "user", "content": message})

        if stream:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
            )
            content = ""
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        chunk_content = delta.content
                        content += chunk_content
                        yield chunk_content
            return content
        else:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=False,
            )
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content or ""
            return ""
