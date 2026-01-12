from abc import ABC, abstractmethod
from typing import Tuple, Optional

from utils.config import get_config
from utils.constants import DEFAULT_DOCUMENT_TYPE
from utils.exceptions import APIError
from utils.prompt_manager import get_prompt


class BaseAPIClient(ABC):
    def __init__(self, api_key: str, default_model: str):
        self.api_key = api_key
        self.default_model = default_model
    
    @abstractmethod
    def initialize(self) -> bool:
        pass
    
    @abstractmethod
    def _generate_content(self, prompt: str, model_name: str) -> Tuple[str, int, int]:
        pass
    
    def create_summary_prompt(self, medical_text: str, additional_info: str = "",
                            department: str = "default", document_type: str = DEFAULT_DOCUMENT_TYPE,
                            doctor: str = "default", previous_record: str = "") -> str:
        prompt_data = get_prompt(department, document_type, doctor)

        if not prompt_data:
            config = get_config()
            prompt_template = config['PROMPTS']['summary']
        else:
            prompt_template = prompt_data['content']

        prompt = f"{prompt_template}\n\n【前回の記載】\n{previous_record}\n\n【カルテ情報】\n{medical_text}\n\n【追加情報】\n{additional_info}"
        return prompt
    
    def get_model_name(self, department: str, document_type: str, doctor: str) -> str:
        prompt_data = get_prompt(department, document_type, doctor)
        return prompt_data.get("selected_model") if prompt_data and prompt_data.get(
            "selected_model") else self.default_model
    
    def generate_summary(
            self, medical_text: str,
            additional_info: str = "",
            department: str = "default",
            document_type: str = DEFAULT_DOCUMENT_TYPE,
            doctor: str = "default",
            model_name: Optional[str] = None,
            previous_record: str = ""
    ) -> Tuple[str, int, int]:
        try:
            self.initialize()

            if not model_name:
                model_name = self.get_model_name(department, document_type, doctor)

            prompt = self.create_summary_prompt(medical_text, additional_info, department, document_type, doctor, previous_record)

            return self._generate_content(prompt, model_name)

        except APIError as e:
            raise e
        except Exception as e:
            raise APIError(f"{self.__class__.__name__}でエラーが発生しました: {str(e)}")
