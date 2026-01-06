from typing import Optional

from google import genai

from .base import BaseProvider, ModelInfo


class GeminiProvider(BaseProvider):
    """Google Gemini API provider."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self._client: Optional[genai.Client] = None

    @property
    def name(self) -> str:
        return "Gemini"

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def list_models(self) -> list[ModelInfo]:
        """List all available models from Gemini."""
        models = []
        for model in self.client.models.list():
            models.append(
                ModelInfo(
                    id=model.name if hasattr(model, "name") else str(model),
                    name=model.display_name if hasattr(model, "display_name") else None,
                    description=model.description if hasattr(model, "description") else None,
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
