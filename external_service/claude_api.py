import os
from typing import Tuple

from anthropic import AnthropicBedrock
from dotenv import load_dotenv

from external_service.base_api import BaseAPIClient
from utils.constants import MESSAGES
from utils.exceptions import APIError

load_dotenv()


class ClaudeAPIClient(BaseAPIClient):
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL")

        super().__init__(None, self.anthropic_model)
        self.client = None

    def initialize(self) -> bool:
        try:
            if not all([self.aws_access_key_id, self.aws_secret_access_key, self.aws_region]):
                raise APIError(MESSAGES["AWS_CREDENTIALS_MISSING"])

            if not self.anthropic_model:
                raise APIError(MESSAGES["ANTHROPIC_MODEL_MISSING"])

            self.client = AnthropicBedrock(
                aws_access_key=self.aws_access_key_id,
                aws_secret_key=self.aws_secret_access_key,
                aws_region=self.aws_region,
            )
            return True

        except Exception as e:
            raise APIError(MESSAGES["BEDROCK_INIT_ERROR"].format(error=str(e)))

    def _generate_content(self, prompt: str, model_name: str) -> Tuple[str, int, int]:
        """
        プロンプトから要約を生成します。
        Args:
            prompt: 生成用プロンプト
            model_name: 使用するモデル名
        Returns:
            Tuple[str, int, int]: (生成された要約, 入力トークン数, 出力トークン数)
        Raises:
            APIError: API呼び出しに失敗した場合
        """
        try:
            response = self.client.messages.create(
                model=model_name,
                max_tokens=6000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            if response.content:
                summary_text = response.content[0].text
            else:
                summary_text = MESSAGES["EMPTY_RESPONSE"]

            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            return summary_text, input_tokens, output_tokens

        except Exception as e:
            raise APIError(MESSAGES["BEDROCK_API_ERROR"].format(error=str(e)))
