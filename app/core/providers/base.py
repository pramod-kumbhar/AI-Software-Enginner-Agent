from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, AsyncIterator
from pydantic import BaseModel
from app.schemas.configuration import ProviderHealthResponse

T = TypeVar("T", bound=BaseModel)

class LLMProvider(ABC):
    """Abstract interface for all Large Language Model inference providers."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the unique name of the provider (e.g. 'ollama', 'mock', 'groq')."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Returns the default model configured for this provider."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        schema: Type[T],
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> T:
        """Generates a structured Pydantic response adhering to the given schema."""
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> str:
        """Generates plain text response."""
        pass

    @abstractmethod
    async def stream_text(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> AsyncIterator[str]:
        """Streams text chunks from the provider."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Estimates or calculates token count for a given text."""
        pass

    @abstractmethod
    async def health_check(self) -> ProviderHealthResponse:
        """Performs a health check on the provider without leaking credentials."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Returns metadata about the active model."""
        pass


class EmbeddingProvider(ABC):
    """Abstract interface for document and query embedding generation."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a list of document strings."""
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Generates an embedding vector for a single search query."""
        pass

    @abstractmethod
    async def health_check(self) -> ProviderHealthResponse:
        pass
