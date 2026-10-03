from abc import ABC, abstractmethod

from common.types.llm import LLMRequest, LLMResponse



class LLMProviderError(Exception):
    """Base error for all LLM provider failures."""


class LLMConnectionError(LLMProviderError):
    """Provider could not be reached."""


class LLMTimeoutError(LLMProviderError):
    """Provider request timed out."""


class LLMAuthenticationError(LLMProviderError):
    """Provider authentication failed."""


class LLMRequestError(LLMProviderError):
    """Provider rejected or could not process the request."""


class LLMProvider(ABC):

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:

        raise NotImplementedError