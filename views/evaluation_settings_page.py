import streamlit as st

from services.evaluation_service import create_or_update_evaluation_prompt, get_evaluation_prompt
from ui_components.navigation import change_page
from utils.config import get_config
from utils.constants import DEFAULT_DOCUMENT_TYPE, DOCUMENT_TYPES
from utils.error_handlers import handle_error
from utils.exceptions import AppError


def _get_default_evaluation_prompts() -> dict:
    config = get_config()
    if config.has_section("EVALUATION_PROMPTS"):
        return dict(config.items("EVALUATION_PROMPTS"))
    return {}


def _render_evaluation_form(document_type: str) -> None:
    prompt_data = get_evaluation_prompt(document_type)
    existing_content = prompt_data.get("content", "") if prompt_data else ""

    if not existing_content:
        st.info(f"{document_type}の評価プロンプトを設定してください。")

    default_prompt = _get_default_evaluation_prompts().get(document_type, "")

    with st.form(key=f"evaluation_prompt_form_{document_type}"):
        prompt_content = st.text_area(
            "プロンプト内容",
            value=existing_content if existing_content else default_prompt,
            height=200,
            key=f"evaluation_prompt_content_{document_type}",
            help="評価プロンプトを入力してください"
        )

        submit = st.form_submit_button("保存", type="primary")

        if submit and prompt_content:
            success, message = create_or_update_evaluation_prompt(document_type, prompt_content)
            if success:
                st.session_state.success_message = message
                st.rerun()
            else:
                raise AppError(message)


@handle_error
def evaluation_settings_ui():
    if "selected_doc_type_for_evaluation" not in st.session_state:
        st.session_state.selected_doc_type_for_evaluation = DEFAULT_DOCUMENT_TYPE

    document_types = DOCUMENT_TYPES
    if not document_types:
        document_types = [DEFAULT_DOCUMENT_TYPE]

    if st.session_state.get("success_message"):
        st.success(st.session_state.success_message)
        st.session_state.success_message = None

    if st.button("作成画面に戻る", key="back_to_main_from_evaluation"):
        change_page("main")
        st.rerun()

    selected_doc_type = st.selectbox(
        "文書名",
        document_types,
        index=document_types.index(st.session_state.selected_doc_type_for_evaluation) if st.session_state.selected_doc_type_for_evaluation in document_types else 0,
        key="evaluation_document_type_selector"
    )
    st.session_state.selected_doc_type_for_evaluation = selected_doc_type

    _render_evaluation_form(selected_doc_type)
