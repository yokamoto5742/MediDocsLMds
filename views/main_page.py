import streamlit as st

from services.evaluation_service import process_evaluation
from services.summary_service import process_summary
from utils.constants import DEFAULT_DOCUMENT_TYPE, DEFAULT_SECTION_NAMES, MESSAGES, TAB_NAMES
from utils.error_handlers import handle_error
from ui_components.navigation import render_sidebar


def clear_inputs():
    st.session_state.current_prescription = ""
    st.session_state.input_text = ""
    st.session_state.additional_info = ""
    st.session_state.output_summary = ""
    st.session_state.parsed_summary = {}
    st.session_state.summary_generation_time = None
    st.session_state.evaluation_result = ""
    st.session_state.evaluation_processing_time = None
    st.session_state.evaluation_just_completed = False
    st.session_state.clear_input = True

    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith("input_text"):
            st.session_state[key] = ""


def render_input_section():
    if "clear_input" not in st.session_state:
        st.session_state.clear_input = False

    current_prescription = st.text_area(
        "退院時処方(現在の処方)",
        height=70,
        key="current_prescription"
    )

    input_text = st.text_area(
        "カルテ記載",
        height=70,
        key="input_text"
    )

    additional_info = st.text_area(
        "追加情報",
        height=70,
        key="additional_info"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("作成", type="primary"):
            process_summary(input_text, additional_info, current_prescription)

    with col2:
        if st.session_state.output_summary:
            if st.button("出力評価"):
                st.session_state.run_evaluation = True

    with col3:
        if st.button("テキストをクリア", on_click=clear_inputs):
            pass

    evaluation_progress_placeholder = st.empty()

    if st.session_state.get("evaluation_just_completed"):
        st.info(MESSAGES["EVALUATION_COMPLETED"])

    return evaluation_progress_placeholder


def render_summary_results():
    if st.session_state.output_summary:
        if st.session_state.parsed_summary:
            tabs = st.tabs([
                TAB_NAMES["ALL"],
                TAB_NAMES["ADMISSION_PERIOD"],
                TAB_NAMES["CURRENT_ILLNESS"],
                TAB_NAMES["ADMISSION_TESTS"],
                TAB_NAMES["TREATMENT_PROGRESS"],
                TAB_NAMES["DISCHARGE_NOTES"],
                TAB_NAMES["NOTE"]
            ])

            with tabs[0]:
                st.code(st.session_state.output_summary,
                        language=None,
                        height=150
                        )

            for i, section_name in enumerate(DEFAULT_SECTION_NAMES, 1):
                with tabs[i]:
                    section_content = st.session_state.parsed_summary.get(section_name, "")
                    st.code(section_content,
                            language=None,
                            height=150)

        st.info(MESSAGES["COPY_INSTRUCTION"])

        if "summary_generation_time" in st.session_state and st.session_state.summary_generation_time is not None:
            processing_time = st.session_state.summary_generation_time
            st.info(MESSAGES["PROCESSING_TIME"].format(processing_time=processing_time))


def render_evaluation_results():
    if st.session_state.get("evaluation_result"):
        if st.session_state.get("evaluation_just_completed"):
            st.session_state.evaluation_just_completed = False

        st.markdown("---")
        st.code(st.session_state.evaluation_result, language=None, height=200)

        if st.session_state.get("evaluation_processing_time"):
            st.info(f"⏱️ 評価時間: {st.session_state.evaluation_processing_time:.0f}秒")


@handle_error
def main_page_app():
    render_sidebar()
    evaluation_progress_placeholder = render_input_section()
    render_summary_results()

    if st.session_state.get("run_evaluation"):
        document_type = st.session_state.get("selected_document_type", DEFAULT_DOCUMENT_TYPE)
        process_evaluation(
            document_type,
            st.session_state.get("input_text", ""),
            st.session_state.get("current_prescription", ""),
            st.session_state.get("additional_info", ""),
            st.session_state.output_summary,
            evaluation_progress_placeholder
        )
        st.session_state.run_evaluation = False
        st.rerun()

    render_evaluation_results()
