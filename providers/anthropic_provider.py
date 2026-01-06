from typing import Optional, Generator

from anthropic import Anthropic

from .base import BaseProvider, ModelInfo


class AnthropicProvider(BaseProvider):
    """Anthropic API provider."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        super().__init__(api_key, base_url, system_prompt, default_model)
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
            messages.append({"role": "user", "content": f"{system_prompt or self.system_prompt}\n\n{message}"})
        else:
            messages.append({"role": "user", "content": message})

        if stream:
            with self.client.messages.stream(
                model=model,
                max_tokens=4096,
                messages=messages,
            ) as stream_response:
                content = ""
                for chunk in stream_response:
                    if chunk.type == "content_block_delta" and chunk.delta.type == "text_delta":
                        chunk_content = chunk.delta.text
                        content += chunk_content
                        yield chunk_content
            return content
        else:
            response = self.client.messages.create(
                model=model,
                max_tokens=4096,
                messages=messages,
            )
            if response.content and len(response.content) > 0:
                return response.content[0].text or ""
            return ""
