from enum import Enum
from typing import Union

from external_service.base_api import BaseAPIClient
from external_service.claude_api import ClaudeAPIClient
from external_service.gemini_api import GeminiAPIClient
from utils.constants import DEFAULT_DOCUMENT_TYPE, MESSAGES
from utils.exceptions import APIError


class APIProvider(Enum):
    CLAUDE = "claude"
    GEMINI = "gemini"


class APIFactory:
    @staticmethod
    def create_client(provider: Union[APIProvider, str]) -> BaseAPIClient:
        if isinstance(provider, str):
            try:
                provider = APIProvider(provider.lower())
            except ValueError:
                raise APIError(MESSAGES["UNSUPPORTED_API_PROVIDER"].format(provider=provider))
        
        client_mapping = {
            APIProvider.CLAUDE: ClaudeAPIClient,
            APIProvider.GEMINI: GeminiAPIClient,
        }
        
        if provider in client_mapping:
            return client_mapping[provider]()
        else:
            raise APIError(MESSAGES["UNSUPPORTED_API_PROVIDER"].format(provider=provider))
    
    @staticmethod
    def generate_summary_with_provider(provider: Union[APIProvider, str],
                                     medical_text: str,
                                     additional_info: str = "",
                                     department: str = "default",
                                     document_type: str = DEFAULT_DOCUMENT_TYPE,
                                     doctor: str = "default",
                                     model_name: str = None,
                                     current_prescription: str = ""):
        client = APIFactory.create_client(provider)
        return client.generate_summary(
            medical_text, additional_info, department,
            document_type, doctor, model_name, current_prescription
        )


def generate_summary(provider: str, medical_text: str, **kwargs):
    return APIFactory.generate_summary_with_provider(provider, medical_text, **kwargs)
