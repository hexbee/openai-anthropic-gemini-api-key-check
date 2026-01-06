from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Generator


@dataclass
class ModelInfo:
    """Unified model information structure."""
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    created: Optional[int] = None


@dataclass
class ChatMessage:
    """Unified chat message structure."""
    role: str  # "system", "user", "assistant"
    content: str


class BaseProvider(ABC):
    """Base class for API providers."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.system_prompt = system_prompt
        self.default_model = default_model

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @abstractmethod
    def list_models(self) -> list[ModelInfo]:
        """List all available models."""
        pass

    @abstractmethod
    def validate_key(self) -> bool:
        """Validate the API key by attempting to list models."""
        pass

    @abstractmethod
    def chat(
        self,
        message: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        stream: bool = True,
    ) -> Generator[str, None, str]:
        """
        Send a chat message and get response.

        Args:
            message: User message
            model: Model to use (defaults to default_model)
            system_prompt: System prompt (defaults to system_prompt)
            stream: Whether to stream the response

        Yields:
            Chunks of the response (empty when not streaming)
        Returns:
            Complete response content
        """
        pass
