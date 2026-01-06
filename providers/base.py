from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelInfo:
    """Unified model information structure."""
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    created: Optional[int] = None


class BaseProvider(ABC):
    """Base class for API providers."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url

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
