import datetime
from typing import Any, Dict, List, Optional, Tuple

from database.db import DatabaseManager
from database.models import Prompt
from database.schema import initialize_database as init_schema
from utils.config import get_config
from utils.constants import DEFAULT_DEPARTMENT, DEFAULT_DOCUMENT_TYPE, DEPARTMENT_DOCTORS_MAPPING, DOCUMENT_TYPES
from utils.exceptions import AppError, DatabaseError


def get_db_manager() -> DatabaseManager:
    try:
        return DatabaseManager.get_instance()
    except Exception as e:
        raise DatabaseError(f"データベース接続の取得に失敗しました: {str(e)}")


def get_current_datetime() -> datetime.datetime:
    return datetime.datetime.now()


def get_all_departments() -> List[str]:
    return DEFAULT_DEPARTMENT


def get_all_prompts() -> List[Dict[str, Any]]:
    try:
        db_manager = get_db_manager()
        return db_manager.query_all(Prompt, order_by=Prompt.department)
    except Exception as e:
        raise DatabaseError(f"プロンプト一覧の取得に失敗しました: {str(e)}")


def get_prompt(
        department: str = "default",
        document_type: str = DEFAULT_DOCUMENT_TYPE,
        doctor: str = "default"
) -> Optional[Dict[str, Any]]:
    try:
        db_manager = get_db_manager()

        prompt = db_manager.query_one(
            Prompt,
            {
            "department": department,
            "document_type": document_type,
            "doctor": doctor
        })

        if not prompt:
            prompt = db_manager.query_one(
                Prompt,
                {
                "department": "default",
                "document_type": DEFAULT_DOCUMENT_TYPE,
                "doctor": "default",
                "is_default": True
            })

        return prompt

    except Exception as e:
        raise DatabaseError(f"プロンプトの取得に失敗しました: {str(e)}")


def create_or_update_prompt(
        department: str,
        document_type: str,
        doctor: str,
        content: str,
        selected_model: Optional[str] = None
) -> Tuple[bool, str]:
    """
    プロンプトを作成または更新する（ORM使用）

    Args:
        department: 診療科
        document_type: 文書タイプ
        doctor: 医師名
        content: プロンプト内容
        selected_model: 選択されたモデル

    Returns:
        (成功フラグ, メッセージ)のタプル
    """
    try:
        if not department or not document_type or not doctor or not content:
            return False, "すべての項目を入力してください"

        db_manager = get_db_manager()

        filters = {
            "department": department,
            "document_type": document_type,
            "doctor": doctor
        }

        existing = db_manager.query_one(Prompt, filters)

        if existing:
            db_manager.update(
                Prompt,
                filters,
                {
                "content": content,
                "selected_model": selected_model
            })
            return True, "プロンプトを更新しました"
        else:
            now = get_current_datetime()
            db_manager.insert(
                Prompt,
                {
                "department": department,
                "document_type": document_type,
                "doctor": doctor,
                "content": content,
                "selected_model": selected_model,
                "is_default": False,
                "created_at": now,
                "updated_at": now
            })
            return True, "プロンプトを新規作成しました"

    except DatabaseError as e:
        return False, str(e)
    except Exception as e:
        raise AppError(f"プロンプトの作成または更新中にエラーが発生しました: {str(e)}")


def delete_prompt(
        department: str,
        document_type: str,
        doctor: str
) -> Tuple[bool, str]:
    try:
        if department == "default" and document_type == DEFAULT_DOCUMENT_TYPE and doctor == "default":
            return False, "デフォルトプロンプトは削除できません"

        db_manager = get_db_manager()

        deleted = db_manager.delete(
            Prompt,
            {
            "department": department,
            "document_type": document_type,
            "doctor": doctor
        })

        if deleted:
            return True, "プロンプトを削除しました"
        else:
            return False, "プロンプトが見つかりません"

    except DatabaseError as e:
        return False, str(e)
    except Exception as e:
        raise AppError(f"プロンプトの削除中にエラーが発生しました: {str(e)}")


def initialize_default_prompt() -> None:
    try:
        db_manager = get_db_manager()

        default_prompt = db_manager.query_one(
            Prompt,
            {
            "department": "default",
            "document_type": DEFAULT_DOCUMENT_TYPE,
            "doctor": "default",
            "is_default": True
        })

        if not default_prompt:
            config = get_config()
            default_prompt_content = config['PROMPTS']['summary']
            now = get_current_datetime()

            db_manager.insert(
                Prompt, {
                "department": "default",
                "document_type": DEFAULT_DOCUMENT_TYPE,
                "doctor": "default",
                "content": default_prompt_content,
                "is_default": True,
                "created_at": now,
                "updated_at": now
            })

    except Exception as e:
        raise DatabaseError(f"デフォルトプロンプトの初期化に失敗しました: {str(e)}")


def initialize_database() -> None:
    try:
        init_schema()
        initialize_default_prompt()

        db_manager = get_db_manager()
        config = get_config()
        default_prompt_content = config['PROMPTS']['summary']
        departments = DEFAULT_DEPARTMENT
        document_types = DOCUMENT_TYPES

        for dept in departments:
            doctors = DEPARTMENT_DOCTORS_MAPPING.get(dept, ["default"])
            for doctor in doctors:
                for doc_type in document_types:
                    existing = db_manager.query_one(
                        Prompt,
                        {
                        "department": dept,
                        "document_type": doc_type,
                        "doctor": doctor
                    })

                    if not existing:
                        now = get_current_datetime()
                        db_manager.insert(
                            Prompt,
                            {
                            "department": dept,
                            "document_type": doc_type,
                            "doctor": doctor,
                            "content": default_prompt_content,
                            "is_default": False,
                            "created_at": now,
                            "updated_at": now
                        })

    except Exception as e:
        raise DatabaseError(f"データベースの初期化に失敗しました: {str(e)}")
