import datetime
from typing import Any, Dict, List

import pandas as pd
import pytz
import streamlit as st
from sqlalchemy import and_, func

from database.db import DatabaseManager
from database.models import SummaryUsage
from ui_components.navigation import change_page
from utils.constants import DOCUMENT_TYPE_OPTIONS
from utils.error_handlers import handle_error
from utils.exceptions import DatabaseError

JST = pytz.timezone('Asia/Tokyo')

MODEL_MAPPING = {
    "Gemini_Pro": "gemini",
    "Claude": "claude",
}


def get_usage_statistics(
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
        selected_model: str,
        selected_document_type: str
) -> Dict[str, Any]:

    db_manager = DatabaseManager.get_instance()
    session = db_manager.get_session()

    try:
        # 基本フィルタを構築
        filters = [
            SummaryUsage.date >= start_datetime,
            SummaryUsage.date <= end_datetime
        ]

        # モデルフィルタを追加
        if selected_model != "すべて":
            pattern = MODEL_MAPPING.get(selected_model)
            if pattern:
                filters.append(SummaryUsage.model_detail.ilike(f"%{pattern}%"))

        # 文書タイプフィルタを追加
        if selected_document_type != "すべて":
            if selected_document_type == "不明":
                filters.append(SummaryUsage.document_types.is_(None))
            else:
                filters.append(SummaryUsage.document_types == selected_document_type)

        total_query = session.query(
            func.count(SummaryUsage.id).label("count"),
            func.sum(SummaryUsage.input_tokens).label("total_input_tokens"),
            func.sum(SummaryUsage.output_tokens).label("total_output_tokens"),
            func.sum(SummaryUsage.total_tokens).label("total_tokens")
        ).filter(and_(*filters))

        total_result = total_query.first()

        if not total_result or total_result.count == 0:
            return {"total": None, "by_department": [], "records": []}

        # 診療科・医師・文書タイプ別の統計を取得
        dept_query = session.query(
            func.coalesce(SummaryUsage.department, 'default').label("department"),
            func.coalesce(SummaryUsage.doctor, 'default').label("doctor"),
            SummaryUsage.document_types,
            func.count(SummaryUsage.id).label("count"),
            func.sum(SummaryUsage.input_tokens).label("input_tokens"),
            func.sum(SummaryUsage.output_tokens).label("output_tokens"),
            func.sum(SummaryUsage.total_tokens).label("total_tokens"),
            func.sum(SummaryUsage.processing_time).label("processing_time")
        ).filter(and_(*filters)).group_by(
            SummaryUsage.department,
            SummaryUsage.doctor,
            SummaryUsage.document_types
        ).order_by(func.count(SummaryUsage.id).desc())

        dept_results = dept_query.all()

        # 個別レコードを取得
        records_query = session.query(SummaryUsage).filter(
            and_(*filters)
        ).order_by(SummaryUsage.date.desc())

        records = records_query.all()

        return {
            "total": {
                "count": total_result.count,
                "total_input_tokens": total_result.total_input_tokens,
                "total_output_tokens": total_result.total_output_tokens,
                "total_tokens": total_result.total_tokens
            },
            "by_department": [
                {
                    "department": row.department,
                    "doctor": row.doctor,
                    "document_types": row.document_types,
                    "count": row.count,
                    "input_tokens": row.input_tokens,
                    "output_tokens": row.output_tokens,
                    "total_tokens": row.total_tokens,
                    "processing_time": row.processing_time
                }
                for row in dept_results
            ],
            "records": [
                {
                    "date": record.date,
                    "document_types": record.document_types,
                    "model_detail": record.model_detail,
                    "department": record.department,
                    "doctor": record.doctor,
                    "input_tokens": record.input_tokens,
                    "output_tokens": record.output_tokens,
                    "processing_time": record.processing_time
                }
                for record in records
            ]
        }

    except Exception as e:
        raise DatabaseError(f"統計データの取得に失敗しました: {str(e)}")
    finally:
        session.close()


def format_department_data(dept_stats: List[Dict[str, Any]]) -> pd.DataFrame:
    """診療科別統計データをDataFrameに変換する"""
    data = []
    for stat in dept_stats:
        dept_name = "全科共通" if stat["department"] == "default" else stat["department"]
        doctor_name = "医師共通" if stat["doctor"] == "default" else stat["doctor"]
        document_types = stat["document_types"] or "不明"
        data.append({
            "文書名": document_types,
            "診療科": dept_name,
            "医師名": doctor_name,
            "作成件数": stat["count"],
            "入力トークン": stat["input_tokens"],
            "出力トークン": stat["output_tokens"],
            "合計トークン": stat["total_tokens"],
        })
    return pd.DataFrame(data)


def format_detail_data(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """詳細レコードをDataFrameに変換する"""
    detail_data = []
    for record in records:
        model_detail = str(record.get("model_detail", "")).lower()
        model_info = "Gemini_Pro"

        for model_name, pattern in MODEL_MAPPING.items():
            if pattern in model_detail:
                model_info = model_name
                break

        record_date = record["date"]
        if record_date.tzinfo:
            jst_date = record_date.astimezone(JST)
        else:
            jst_date = JST.localize(record_date)

        detail_data.append({
            "作成日": jst_date.strftime("%Y/%m/%d"),
            "文書名": record.get("document_types") or "不明",
            "診療科": "全科共通" if record.get("department") == "default" else record.get("department"),
            "医師名": "医師共通" if record.get("doctor") == "default" else record.get("doctor"),
            "AIモデル": model_info,
            "入力トークン": record["input_tokens"],
            "出力トークン": record["output_tokens"],
            "処理時間(秒)": round(record["processing_time"]) if record["processing_time"] else 0,
        })
    return pd.DataFrame(detail_data)


@handle_error
def usage_statistics_ui():
    if st.button("作成画面に戻る", key="back_to_main_from_stats"):
        change_page("main")
        st.rerun()

    col1, col2 = st.columns(2)

    with col1:
        today = datetime.datetime.now().date()
        start_date = st.date_input("開始日", today - datetime.timedelta(days=7))

    with col2:
        models = ["すべて", "Claude", "Gemini_Pro"]
        selected_model = st.selectbox("AIモデル", models, index=0)

    col3, col4 = st.columns(2)

    with col3:
        end_date = st.date_input("終了日", today)

    with col4:
        selected_document_type = st.selectbox("文書名", DOCUMENT_TYPE_OPTIONS, index=0)

    start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
    end_datetime = datetime.datetime.combine(end_date, datetime.time.max)

    # 統計データを取得
    stats = get_usage_statistics(start_datetime, end_datetime, selected_model, selected_document_type)

    if stats["total"] is None:
        st.info("指定期間のデータがありません")
        return

    # 診療科別統計を表示
    dept_df = format_department_data(stats["by_department"])
    st.dataframe(dept_df, hide_index=True)

    # 詳細レコードを表示
    detail_df = format_detail_data(stats["records"])
    st.dataframe(detail_df, hide_index=True)
