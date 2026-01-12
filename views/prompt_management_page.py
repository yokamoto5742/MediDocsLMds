import streamlit as st

from utils.constants import DEPARTMENT_DOCTORS_MAPPING, DOCUMENT_TYPES, DEFAULT_DOCUMENT_TYPE
from utils.error_handlers import handle_error
from utils.exceptions import AppError
from utils.prompt_manager import get_all_departments, get_prompt, create_or_update_prompt, delete_prompt
from ui_components.navigation import change_page


def update_document_type():
    st.session_state.selected_doc_type_for_prompt = st.session_state.prompt_document_type_selector

    prompt_data = get_prompt(
        st.session_state.selected_dept_for_prompt,
        st.session_state.selected_doc_type_for_prompt,
        st.session_state.selected_doctor_for_prompt
    )

    if prompt_data and prompt_data.get("selected_model"):
        st.session_state.document_model_mapping[st.session_state.selected_doc_type_for_prompt] = prompt_data.get(
            "selected_model")

    st.session_state.update_ui = True


@handle_error
def prompt_management_ui():
    if st.session_state.success_message:
        st.success(st.session_state.success_message)
        st.session_state.success_message = None

    if st.button("作成画面に戻る", key="back_to_main"):
        change_page("main")
        st.rerun()

    if "selected_dept_for_prompt" not in st.session_state:
        st.session_state.selected_dept_for_prompt = "default"

    if "selected_doc_type_for_prompt" not in st.session_state:
        st.session_state.selected_doc_type_for_prompt = DEFAULT_DOCUMENT_TYPE

    if "selected_doctor_for_prompt" not in st.session_state:
        st.session_state.selected_doctor_for_prompt = "default"

    departments = ["default"] + get_all_departments()
    document_types = DOCUMENT_TYPES
    if not document_types:
        document_types = [DEFAULT_DOCUMENT_TYPE]

    if "document_model_mapping" not in st.session_state:
        st.session_state.document_model_mapping = {}

    col1, col2 = st.columns(2)

    with col1:
        selected_doc_type = st.selectbox(
            "文書名",
            document_types,
            index=document_types.index(
                st.session_state.selected_doc_type_for_prompt) if st.session_state.selected_doc_type_for_prompt in document_types else 0,
            key="prompt_document_type_selector",
            on_change=update_document_type
        )

    selected_dept = st.session_state.selected_dept_for_prompt
    selected_doctor = st.session_state.selected_doctor_for_prompt
    prompt_data = get_prompt(selected_dept, selected_doc_type, selected_doctor)

    available_models = []
    if "available_models" in st.session_state:
        available_models = st.session_state.available_models

    model_options = available_models

    if prompt_data and prompt_data.get("selected_model"):
        selected_model = prompt_data.get("selected_model")
    elif selected_doc_type in st.session_state.document_model_mapping:
        selected_model = st.session_state.document_model_mapping[selected_doc_type]
    else:
        selected_model = model_options[0] if model_options else None

    model_index = 0
    if selected_model in model_options:
        model_index = model_options.index(selected_model)

    with col2:
        prompt_model = st.selectbox(
            "AIモデル",
            model_options,
            index=model_index,
            key=f"prompt_model_{selected_doc_type}",
            on_change=lambda: st.session_state.document_model_mapping.update({selected_doc_type: prompt_model})
        )

    col3, col4 = st.columns(2)
    with col3:
        selected_dept = st.selectbox(
            "診療科",
            departments,
            index=departments.index(
                st.session_state.selected_dept_for_prompt) if st.session_state.selected_dept_for_prompt in departments else 0,
            format_func=lambda x: "全科共通" if x == "default" else x,
            key="prompt_department_selector"
        )

    available_doctors = DEPARTMENT_DOCTORS_MAPPING.get(selected_dept, ["default"])
    if st.session_state.selected_doctor_for_prompt not in available_doctors:
        st.session_state.selected_doctor_for_prompt = available_doctors[0]

    with col4:
        selected_doctor = st.selectbox(
            "医師名",
            available_doctors,
            index=available_doctors.index(st.session_state.selected_doctor_for_prompt),
            format_func=lambda x: "医師共通" if x == "default" else x,
            key="prompt_doctor_selector"
        )

    st.session_state.selected_dept_for_prompt = selected_dept
    st.session_state.selected_doc_type_for_prompt = selected_doc_type
    st.session_state.selected_doctor_for_prompt = selected_doctor
    st.session_state.document_model_mapping[selected_doc_type] = prompt_model

    with st.form(key=f"edit_prompt_form_{selected_dept}_{selected_doc_type}_{selected_doctor}"):
        prompt_content = st.text_area(
            "プロンプト内容",
            value=prompt_data.get("content", "") if prompt_data else "",
            height=200,
            key=f"prompt_content_{selected_dept}_{selected_doc_type}_{selected_doctor}"
        )

        submit = st.form_submit_button("保存")

        if submit:
            if prompt_model:
                st.session_state.document_model_mapping[selected_doc_type] = prompt_model

            success, message = create_or_update_prompt(selected_dept, selected_doc_type, selected_doctor,
                                                       prompt_content, prompt_model)
            if success:
                st.success(message)
            else:
                raise AppError(message)

    if selected_dept != "default" or selected_doc_type != DEFAULT_DOCUMENT_TYPE or selected_doctor != "default":
        if st.button("プロンプトを削除", key=f"delete_prompt_{selected_dept}_{selected_doc_type}_{selected_doctor}",
                     type="primary"):
            success, message = delete_prompt(selected_dept, selected_doc_type, selected_doctor)
            if success:
                st.session_state.success_message = message
                st.session_state.selected_dept_for_prompt = "default"
                st.session_state.selected_doc_type_for_prompt = DEFAULT_DOCUMENT_TYPE
                st.session_state.selected_doctor_for_prompt = "default"
                st.rerun()
            else:
                raise AppError(message)
