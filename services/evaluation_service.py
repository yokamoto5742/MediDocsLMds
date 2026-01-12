import datetime
import queue
import threading
import time
from typing import Any, Dict, Optional, Tuple

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from database.db import DatabaseManager
from database.models import EvaluationPrompt
from external_service.gemini_evaluation import GeminiAPIClient
from utils.config import GEMINI_EVALUATION_MODEL, GOOGLE_CREDENTIALS_JSON
from utils.error_handlers import handle_error
from utils.exceptions import APIError, DatabaseError


def get_evaluation_prompt(document_type: str) -> Optional[Dict[str, Any]]:
    try:
        db_manager = DatabaseManager.get_instance()
        return db_manager.query_one(EvaluationPrompt, {"document_type": document_type})
    except Exception as e:
        raise DatabaseError(f"評価プロンプトの取得に失敗しました: {str(e)}")


def create_or_update_evaluation_prompt(document_type: str, content: str) -> Tuple[bool, str]:
    try:
        if not content:
            return False, "評価プロンプトを作成してください"

        db_manager = DatabaseManager.get_instance()
        existing = db_manager.query_one(EvaluationPrompt, {"document_type": document_type})

        if existing:
            db_manager.update(
                EvaluationPrompt,
                {"document_type": document_type},
                {"content": content, "updated_at": datetime.datetime.now()}
            )
            return True, "評価プロンプトを更新しました"
        else:
            db_manager.insert(
                EvaluationPrompt,
                {
                    "document_type": document_type,
                    "content": content,
                    "is_active": True,
                    "created_at": datetime.datetime.now(),
                    "updated_at": datetime.datetime.now()
                }
            )
            return True, "評価プロンプトを新規作成しました"
    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}"


def build_evaluation_prompt(
    prompt_template: str,
    input_text: str,
    current_prescription: str,
    additional_info: str,
    output_summary: str
) -> str:
    return f"""{prompt_template}

【カルテ記載】
{input_text}

【退院時処方(現在の処方)】
{current_prescription}

【追加情報】
{additional_info}

【生成された出力】
{output_summary}
"""


def evaluate_output_task(
    document_type: str,
    input_text: str,
    current_prescription: str,
    additional_info: str,
    output_summary: str,
    result_queue: queue.Queue
) -> None:
    try:
        prompt_data = get_evaluation_prompt(document_type)
        if not prompt_data:
            raise APIError(f"{document_type}の評価プロンプトが設定されていません。出力評価設定から設定してください。")

        prompt_template = prompt_data.get("content", "")

        full_prompt = build_evaluation_prompt(
            prompt_template,
            input_text,
            current_prescription,
            additional_info,
            output_summary
        )

        if not GEMINI_EVALUATION_MODEL:
            raise APIError("GEMINI_EVALUATION_MODEL が設定されていません。")

        client = GeminiAPIClient()
        client.initialize()

        evaluation_text, input_tokens, output_tokens = client._generate_content(
            full_prompt, GEMINI_EVALUATION_MODEL
        )

        result_queue.put({
            "success": True,
            "evaluation_result": evaluation_text,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        })

    except Exception as e:
        result_queue.put({
            "success": False,
            "error": str(e)
        })


def display_evaluation_progress(
    thread: threading.Thread,
    placeholder: DeltaGenerator,
    start_time: datetime.datetime
) -> None:
    elapsed_time = 0
    with st.spinner("評価中..."):
        placeholder.text(f"⏱️ 評価時間: {elapsed_time}秒")
        while thread.is_alive():
            time.sleep(1)
            elapsed_time = int((datetime.datetime.now() - start_time).total_seconds())
            placeholder.text(f"⏱️ 評価時間: {elapsed_time}秒")


@handle_error
def process_evaluation(
    document_type: str,
    input_text: str,
    current_prescription: str,
    additional_info: str,
    output_summary: str,
    progress_placeholder: DeltaGenerator
) -> None:
    if not GOOGLE_CREDENTIALS_JSON:
        raise APIError("Gemini APIの認証情報が設定されていません。")

    if not GEMINI_EVALUATION_MODEL:
        raise APIError("GEMINI_EVALUATION_MODEL環境変数が設定されていません。")

    if not output_summary:
        st.warning("評価対象の出力がありません。")
        return

    start_time = datetime.datetime.now()
    result_queue = queue.Queue()

    evaluation_thread = threading.Thread(
        target=evaluate_output_task,
        args=(document_type, input_text, current_prescription, additional_info, output_summary, result_queue)
    )
    evaluation_thread.start()

    display_evaluation_progress(evaluation_thread, progress_placeholder, start_time)

    evaluation_thread.join()
    progress_placeholder.empty()
    result = result_queue.get()

    if result["success"]:
        st.session_state.evaluation_result = result["evaluation_result"]
        processing_time = (datetime.datetime.now() - start_time).total_seconds()
        st.session_state.evaluation_processing_time = processing_time
        st.session_state.evaluation_just_completed = True
    else:
        raise APIError(f"評価中にエラーが発生しました: {result['error']}")
