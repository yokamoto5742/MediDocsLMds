import queue
from unittest.mock import Mock, patch

import pytest

# テスト対象のモジュールをインポート
from services.summary_service import (
    generate_summary_task,
    validate_api_credentials,
    validate_input_text,
    get_session_parameters,
    handle_success_result,
    save_usage_to_database,
    normalize_selection_params,
    determine_final_model,
    get_provider_and_model,
    validate_api_credentials_for_provider
)

# テスト用定数
TEST_INPUT_TEXT = "これはテスト用の医療テキストです。" * 100
TEST_ADDITIONAL_INFO = "追加情報です"
TEST_DEPARTMENT = "内科"
TEST_DOCUMENT_TYPE = "診療録"
TEST_DOCTOR = "田中医師"


class TestValidateApiCredentials:
    """API認証情報検証のテストクラス"""

    @patch('services.summary_service.GOOGLE_CREDENTIALS_JSON', None)
    @patch('services.summary_service.CLAUDE_API_KEY', None)
    def test_validate_api_credentials_no_credentials(self):
        """API認証情報が全て未設定の場合のテスト"""
        from utils.exceptions import APIError

        with pytest.raises(APIError):
            validate_api_credentials()

    @patch('services.summary_service.GOOGLE_CREDENTIALS_JSON', 'test_gemini_key')
    @patch('services.summary_service.CLAUDE_API_KEY', None)
    def test_validate_api_credentials_with_gemini(self):
        """Gemini認証情報のみ設定されている場合のテスト"""
        # 例外が発生しないことを確認
        validate_api_credentials()

    @patch('services.summary_service.GOOGLE_CREDENTIALS_JSON', None)
    @patch('services.summary_service.CLAUDE_API_KEY', 'test_claude_key')
    def test_validate_api_credentials_with_claude(self):
        """Claude認証情報のみ設定されている場合のテスト"""
        # 例外が発生しないことを確認
        validate_api_credentials()


class TestValidateInputText:
    """入力テキスト検証のテストクラス"""

    @patch('streamlit.warning')
    def test_validate_input_text_empty(self, mock_warning):
        """空の入力テキストのテスト"""
        validate_input_text("")
        mock_warning.assert_called_once()

    @patch('streamlit.warning')
    @patch('services.summary_service.MIN_INPUT_TOKENS', 100)
    def test_validate_input_text_too_short(self, mock_warning):
        """入力テキストが短すぎる場合のテスト"""
        validate_input_text("短いテキスト")
        mock_warning.assert_called_once()

    @patch('streamlit.warning')
    @patch('services.summary_service.MAX_INPUT_TOKENS', 50)
    def test_validate_input_text_too_long(self, mock_warning):
        """入力テキストが長すぎる場合のテスト"""
        long_text = "長いテキスト" * 20
        validate_input_text(long_text)
        mock_warning.assert_called_once()

    @patch('streamlit.warning')
    @patch('services.summary_service.MIN_INPUT_TOKENS', 10)
    @patch('services.summary_service.MAX_INPUT_TOKENS', 1000)
    def test_validate_input_text_valid(self, mock_warning):
        """正常な入力テキストのテスト"""
        validate_input_text("適切な長さのテキストです")
        mock_warning.assert_not_called()


class TestNormalizeSelectionParams:
    """パラメータ正規化のテストクラス"""

    @patch('services.summary_service.DEFAULT_DEPARTMENT', ['内科', '外科', 'default'])
    @patch('services.summary_service.DOCUMENT_TYPES', ['診療録', 'サマリー'])
    def test_normalize_selection_params_valid(self):
        """正常なパラメータの正規化テスト"""
        dept, doc_type = normalize_selection_params('内科', '診療録')
        assert dept == '内科'
        assert doc_type == '診療録'

    @patch('services.summary_service.DEFAULT_DEPARTMENT', ['内科', '外科', 'default'])
    @patch('services.summary_service.DOCUMENT_TYPES', ['診療録', 'サマリー'])
    def test_normalize_selection_params_invalid_department(self):
        """無効な診療科の正規化テスト"""
        dept, doc_type = normalize_selection_params('無効な診療科', '診療録')
        assert dept == 'default'
        assert doc_type == '診療録'

    @patch('services.summary_service.DEFAULT_DEPARTMENT', ['内科', '外科', 'default'])
    @patch('services.summary_service.DOCUMENT_TYPES', ['診療録', 'サマリー'])
    def test_normalize_selection_params_invalid_document_type(self):
        """無効な文書タイプの正規化テスト"""
        dept, doc_type = normalize_selection_params('内科', '無効なタイプ')
        assert dept == '内科'
        assert doc_type == '診療録'  # DOCUMENT_TYPES[0]


class TestGetProviderAndModel:
    """プロバイダーとモデル取得のテストクラス"""

    @patch('services.summary_service.ANTHROPIC_MODEL', 'claude-3-sonnet')
    @patch('services.summary_service.GEMINI_MODEL', 'gemini-pro')
    def test_get_provider_and_model_claude(self):
        """Claudeモデルの取得テスト"""
        provider, model = get_provider_and_model('Claude')
        assert provider == 'claude'
        assert model == 'claude-3-sonnet'

    @patch('services.summary_service.GEMINI_MODEL', 'gemini-pro')
    def test_get_provider_and_model_gemini_pro(self):
        """Gemini Proモデルの取得テスト"""
        provider, model = get_provider_and_model('Gemini_Pro')
        assert provider == 'gemini'
        assert model == 'gemini-pro'


    def test_get_provider_and_model_invalid(self):
        """無効なモデルの取得テスト"""
        from utils.exceptions import APIError

        with pytest.raises(APIError):
            get_provider_and_model('InvalidModel')


class TestValidateApiCredentialsForProvider:
    """プロバイダー固有の認証情報検証テストクラス"""

    @patch('services.summary_service.CLAUDE_API_KEY', 'test_claude_key')
    def test_validate_api_credentials_for_provider_claude_valid(self):
        """Claude認証情報が有効な場合のテスト"""
        # 例外が発生しないことを確認
        validate_api_credentials_for_provider('claude')

    @patch('services.summary_service.CLAUDE_API_KEY', None)
    def test_validate_api_credentials_for_provider_claude_invalid(self):
        """Claude認証情報が無効な場合のテスト"""
        from utils.exceptions import APIError

        with pytest.raises(APIError):
            validate_api_credentials_for_provider('claude')

    @patch('services.summary_service.GOOGLE_CREDENTIALS_JSON', 'test_gemini_creds')
    def test_validate_api_credentials_for_provider_gemini_valid(self):
        """Gemini認証情報が有効な場合のテスト"""
        # 例外が発生しないことを確認
        validate_api_credentials_for_provider('gemini')



class TestDetermineFinalModel:
    """最終モデル決定のテストクラス"""

    @patch('services.summary_service.get_prompt')
    @patch('services.summary_service.MAX_TOKEN_THRESHOLD', 1000)
    def test_determine_final_model_no_prompt_model(self, mock_get_prompt):
        """プロンプトでモデルが指定されていない場合のテスト"""
        mock_get_prompt.return_value = {'selected_model': None}

        model, switched, original = determine_final_model(
            '内科', '診療録', '医師', 'Claude', False, 'テスト', ''
        )

        assert model == 'Claude'
        assert switched == False
        assert original == 'Claude'

    @patch('services.summary_service.get_prompt')
    @patch('services.summary_service.MAX_TOKEN_THRESHOLD', 1000)
    def test_determine_final_model_with_prompt_model(self, mock_get_prompt):
        """プロンプトでモデルが指定されている場合のテスト"""
        mock_get_prompt.return_value = {'selected_model': 'Gemini_Pro'}

        model, switched, original = determine_final_model(
            '内科', '診療録', '医師', 'Claude', False, 'テスト', ''
        )

        assert model == 'Gemini_Pro'
        assert switched == False
        assert original == 'Gemini_Pro'

    @patch('services.summary_service.get_prompt')
    @patch('services.summary_service.MAX_TOKEN_THRESHOLD', 10)
    @patch('services.summary_service.GOOGLE_CREDENTIALS_JSON', 'test_creds')
    @patch('services.summary_service.GEMINI_MODEL', 'gemini-pro')
    def test_determine_final_model_token_threshold_exceeded(self, mock_get_prompt):
        """トークン数制限を超えた場合のモデル切り替えテスト"""
        mock_get_prompt.return_value = None

        model, switched, original = determine_final_model(
            '内科', '診療録', '医師', 'Claude', False, 'とても長いテキスト' * 100, ''
        )

        assert model == 'Gemini_Pro'
        assert switched == True
        assert original == 'Claude'

    @patch('services.summary_service.get_prompt')
    @patch('services.summary_service.MAX_TOKEN_THRESHOLD', 10)
    @patch('services.summary_service.GOOGLE_CREDENTIALS_JSON', None)
    def test_determine_final_model_token_threshold_exceeded_no_gemini(self, mock_get_prompt):
        """トークン数制限を超えたがGeminiが利用できない場合のテスト"""
        mock_get_prompt.return_value = None
        from utils.exceptions import APIError

        with pytest.raises(APIError):
            determine_final_model(
                '内科', '診療録', '医師', 'Claude', False, 'とても長いテキスト' * 100, ''
            )


class TestGetSessionParameters:
    """セッションパラメータ取得のテストクラス"""

    @patch('services.summary_service.st.session_state')
    def test_get_session_parameters(self, mock_session_state):
        """セッションパラメータの取得テスト"""
        # session_stateの属性を設定
        type(mock_session_state).available_models = ['Claude', 'Gemini_Pro']
        type(mock_session_state).selected_model = 'Claude'
        type(mock_session_state).selected_department = '内科'
        type(mock_session_state).selected_document_type = '診療録'
        type(mock_session_state).selected_doctor = '田中医師'
        type(mock_session_state).model_explicitly_selected = True

        params = get_session_parameters()

        assert params['available_models'] == ['Claude', 'Gemini_Pro']
        assert params['selected_model'] == 'Claude'
        assert params['selected_department'] == '内科'
        assert params['selected_document_type'] == '診療録'
        assert params['selected_doctor'] == '田中医師'
        assert params['model_explicitly_selected'] == True


class TestGenerateSummaryTask:
    """サマリー生成タスクのテストクラス"""

    @patch('services.summary_service.normalize_selection_params')
    @patch('services.summary_service.determine_final_model')
    @patch('services.summary_service.get_provider_and_model')
    @patch('services.summary_service.validate_api_credentials_for_provider')
    @patch('services.summary_service.generate_summary')
    @patch('services.summary_service.format_output_summary')
    @patch('services.summary_service.parse_output_summary')
    def test_generate_summary_task_success(
            self, mock_parse, mock_format, mock_generate, mock_validate,
            mock_get_provider, mock_determine, mock_normalize
    ):
        """サマリー生成タスクの成功テスト"""
        # モックの設定
        mock_normalize.return_value = ('内科', '診療録')
        mock_determine.return_value = ('Claude', False, 'Claude')
        mock_get_provider.return_value = ('claude', 'claude-3-sonnet')
        mock_generate.return_value = ('生成されたサマリー', 100, 200)
        mock_format.return_value = 'フォーマット済みサマリー'
        mock_parse.return_value = {'summary': 'パース済みサマリー'}

        result_queue = queue.Queue()

        generate_summary_task(TEST_INPUT_TEXT, '内科', 'Claude', result_queue, TEST_ADDITIONAL_INFO, '診療録',
                              '田中医師')

        result = result_queue.get()

        assert result['success'] == True
        assert result['output_summary'] == 'フォーマット済みサマリー'
        assert result['parsed_summary'] == {'summary': 'パース済みサマリー'}
        assert result['input_tokens'] == 100
        assert result['output_tokens'] == 200
        assert result['model_detail'] == 'Claude'  # providerが'gemini'以外の場合はfinal_modelが使用される
        assert result['model_switched'] == False
        assert result['original_model'] is None

    @patch('services.summary_service.normalize_selection_params')
    def test_generate_summary_task_exception(self, mock_normalize):
        """サマリー生成タスクの例外処理テスト"""
        mock_normalize.side_effect = Exception("Test Error")

        result_queue = queue.Queue()

        from utils.exceptions import APIError
        with pytest.raises(APIError):
            generate_summary_task(
                TEST_INPUT_TEXT, '内科', 'Claude', result_queue
            )

        result = result_queue.get()

        assert result['success'] == False
        assert isinstance(result['error'], str)



class TestSaveUsageToDatabase:
    """データベース保存のテストクラス"""

    @patch('services.summary_service.DatabaseManager')
    @patch('streamlit.warning')
    def test_save_usage_to_database_success(self, mock_warning, mock_db_manager):
        """データベース保存成功のテスト"""
        from database.models import SummaryUsage
        mock_db_instance = Mock()
        mock_db_manager.get_instance.return_value = mock_db_instance
        mock_db_instance.insert.return_value = {"id": 1}

        result = {
            'model_detail': 'claude-3-sonnet',
            'input_tokens': 100,
            'output_tokens': 200,
            'processing_time': 5.5
        }

        session_params = {
            'selected_document_type': '診療録',
            'selected_department': '内科',
            'selected_doctor': '田中医師'
        }

        save_usage_to_database(result, session_params)

        mock_db_instance.insert.assert_called_once()
        call_args = mock_db_instance.insert.call_args
        assert call_args[0][0] == SummaryUsage
        mock_warning.assert_not_called()

    @patch('services.summary_service.DatabaseManager')
    @patch('streamlit.warning')
    def test_save_usage_to_database_exception(self, mock_warning, mock_db_manager):
        """データベース保存エラーのテスト"""
        mock_db_manager.get_instance.side_effect = Exception("DB接続エラー")

        result = {
            'model_detail': 'claude-3-sonnet',
            'input_tokens': 100,
            'output_tokens': 200,
            'processing_time': 5.5
        }

        session_params = {
            'selected_document_type': '診療録',
            'selected_department': '内科',
            'selected_doctor': '田中医師'
        }

        save_usage_to_database(result, session_params)

        mock_warning.assert_called_once()


class TestHandleSuccessResult:
    """成功結果処理のテストクラス"""

    @patch('streamlit.session_state')
    @patch('streamlit.info')
    @patch('services.summary_service.save_usage_to_database')
    def test_handle_success_result_no_model_switch(
            self, mock_save, mock_info, mock_session_state
    ):
        """モデル切り替えなしの成功結果処理テスト"""
        result = {
            'output_summary': 'テストサマリー',
            'parsed_summary': {'summary': 'パース済み'},
            'model_switched': False
        }

        session_params = {'selected_department': '内科'}

        handle_success_result(result, session_params)

        assert mock_session_state.output_summary == 'テストサマリー'
        assert mock_session_state.parsed_summary == {'summary': 'パース済み'}
        mock_info.assert_not_called()
        mock_save.assert_called_once_with(result, session_params)

    @patch('streamlit.session_state')
    @patch('streamlit.info')
    @patch('services.summary_service.save_usage_to_database')
    def test_handle_success_result_with_model_switch(
            self, mock_save, mock_info, mock_session_state
    ):
        """モデル切り替えありの成功結果処理テスト"""
        result = {
            'output_summary': 'テストサマリー',
            'parsed_summary': {'summary': 'パース済み'},
            'model_switched': True,
            'original_model': 'Claude'
        }

        session_params = {'selected_department': '内科'}

        handle_success_result(result, session_params)

        assert mock_session_state.output_summary == 'テストサマリー'
        assert mock_session_state.parsed_summary == {'summary': 'パース済み'}
        mock_info.assert_called_once()
        mock_save.assert_called_once_with(result, session_params)


# フィクスチャーの定義
@pytest.fixture
def sample_result():
    """テスト用の結果データ"""
    return {
        'success': True,
        'output_summary': 'テストサマリー',
        'parsed_summary': {'summary': 'パース済み'},
        'input_tokens': 100,
        'output_tokens': 200,
        'model_detail': 'claude-3-sonnet',
        'model_switched': False,
        'original_model': None,
        'processing_time': 5.0
    }


@pytest.fixture
def sample_session_params():
    """テスト用のセッションパラメータ"""
    return {
        'available_models': ['Claude', 'Gemini_Pro'],
        'selected_model': 'Claude',
        'selected_department': '内科',
        'selected_document_type': '診療録',
        'selected_doctor': '田中医師',
        'model_explicitly_selected': False
    }


if __name__ == "__main__":
    pytest.main([__file__])