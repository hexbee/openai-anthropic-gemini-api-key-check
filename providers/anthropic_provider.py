from typing import Optional

from anthropic import Anthropic

from .base import BaseProvider, ModelInfo


class AnthropicProvider(BaseProvider):
    """Anthropic API provider."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self._client: Optional[Anthropic] = None

    @property
    def name(self) -> str:
        return "Anthropic"

    @property
    def client(self) -> Anthropic:
        if self._client is None:
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = Anthropic(**kwargs)
        return self._client

    def list_models(self) -> list[ModelInfo]:
        """List all available models from Anthropic."""
        models = []
        for model in self.client.models.list():
            models.append(
                ModelInfo(
                    id=model.id,
                    name=model.display_name if hasattr(model, "display_name") else model.id,
                    description=getattr(model, "description", None),
                    created=int(model.created_at.timestamp()) if hasattr(model, "created_at") and model.created_at else None,
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
