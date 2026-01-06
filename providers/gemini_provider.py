from typing import Optional, Generator

from google import genai

from .base import BaseProvider, ModelInfo


class GeminiProvider(BaseProvider):
    """Google Gemini API provider."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        super().__init__(api_key, base_url, system_prompt, default_model)
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

        prompt = message
        if system_prompt or self.system_prompt:
            prompt = f"{system_prompt or self.system_prompt}\n\nUser: {message}"

        if stream:
            response = self.client.models.generate_content_stream(
                model=model,
                contents=prompt,
            )
            content = ""
            for chunk in response:
                if chunk.text:
                    chunk_content = chunk.text
                    content += chunk_content
                    yield chunk_content
            return content
        else:
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
            )
            if response.text:
                return response.text
            return ""
