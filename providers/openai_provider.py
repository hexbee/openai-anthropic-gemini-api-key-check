from typing import Optional

from openai import OpenAI

from .base import BaseProvider, ModelInfo


class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
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
