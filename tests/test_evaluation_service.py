import datetime
import queue
import threading
from unittest.mock import Mock, patch, MagicMock

import pytest

from database.models import EvaluationPrompt
from services.evaluation_service import (
    build_evaluation_prompt,
    create_or_update_evaluation_prompt,
    display_evaluation_progress,
    evaluate_output_task,
    get_evaluation_prompt,
    process_evaluation
)
from utils.exceptions import APIError, DatabaseError


class TestGetEvaluationPrompt:
    """評価プロンプト取得のテストクラス"""

    @patch('services.evaluation_service.DatabaseManager')
    def test_get_evaluation_prompt_success(self, mock_db_manager):
        """評価プロンプト取得成功のテスト"""
        mock_db_instance = Mock()
        mock_db_manager.get_instance.return_value = mock_db_instance
        mock_db_instance.query_one.return_value = {
            'document_type': '診療録',
            'content': 'テスト評価プロンプト',
            'is_active': True
        }

        result = get_evaluation_prompt('診療録')

        assert result is not None
        assert result['document_type'] == '診療録'
        assert result['content'] == 'テスト評価プロンプト'
        mock_db_instance.query_one.assert_called_once_with(
            EvaluationPrompt,
            {'document_type': '診療録'}
        )

    @patch('services.evaluation_service.DatabaseManager')
    def test_get_evaluation_prompt_not_found(self, mock_db_manager):
        """評価プロンプトが存在しない場合のテスト"""
        mock_db_instance = Mock()
        mock_db_manager.get_instance.return_value = mock_db_instance
        mock_db_instance.query_one.return_value = None

        result = get_evaluation_prompt('存在しない文書タイプ')

        assert result is None

    @patch('services.evaluation_service.DatabaseManager')
    def test_get_evaluation_prompt_database_error(self, mock_db_manager):
        """データベースエラーのテスト"""
        mock_db_instance = Mock()
        mock_db_manager.get_instance.return_value = mock_db_instance
        mock_db_instance.query_one.side_effect = Exception("DB接続エラー")

        with pytest.raises(DatabaseError) as exc_info:
            get_evaluation_prompt('診療録')

        assert "評価プロンプトの取得に失敗しました" in str(exc_info.value)


class TestCreateOrUpdateEvaluationPrompt:
    """評価プロンプト作成/更新のテストクラス"""

    @patch('services.evaluation_service.DatabaseManager')
    def test_create_evaluation_prompt_success(self, mock_db_manager):
        """評価プロンプト新規作成成功のテスト"""
        mock_db_instance = Mock()
        mock_db_manager.get_instance.return_value = mock_db_instance
        mock_db_instance.query_one.return_value = None
        mock_db_instance.insert.return_value = {'id': 1}

        success, message = create_or_update_evaluation_prompt(
            '診療録',
            'テスト評価プロンプト内容'
        )

        assert success is True
        assert '新規作成' in message
        mock_db_instance.insert.assert_called_once()

    @patch('services.evaluation_service.DatabaseManager')
    def test_update_evaluation_prompt_success(self, mock_db_manager):
        """評価プロンプト更新成功のテスト"""
        mock_db_instance = Mock()
        mock_db_manager.get_instance.return_value = mock_db_instance
        mock_db_instance.query_one.return_value = {
            'document_type': '診療録',
            'content': '古いプロンプト'
        }
        mock_db_instance.update.return_value = True

        success, message = create_or_update_evaluation_prompt(
            '診療録',
            '更新されたプロンプト'
        )

        assert success is True
        assert '更新' in message
        mock_db_instance.update.assert_called_once()

    def test_create_or_update_evaluation_prompt_empty_content(self):
        """空のプロンプト内容のテスト"""
        success, message = create_or_update_evaluation_prompt('診療録', '')

        assert success is False
        assert 'プロンプトを入力してください' in message

    @patch('services.evaluation_service.DatabaseManager')
    def test_create_or_update_evaluation_prompt_database_error(self, mock_db_manager):
        """データベースエラーのテスト"""
        mock_db_instance = Mock()
        mock_db_manager.get_instance.return_value = mock_db_instance
        mock_db_instance.query_one.side_effect = Exception("DB接続エラー")

        success, message = create_or_update_evaluation_prompt(
            '診療録',
            'テスト内容'
        )

        assert success is False
        assert 'エラーが発生しました' in message


class TestBuildEvaluationPrompt:
    """評価プロンプト構築のテストクラス"""

    def test_build_evaluation_prompt_basic(self):
        """基本的な評価プロンプト構築のテスト"""
        prompt_template = "以下の情報を評価してください："
        current_prescription = "退院時処方内容"
        input_text = "今回の診療内容"
        additional_info = "追加の情報"
        output_summary = "生成されたサマリー"

        result = build_evaluation_prompt(
            prompt_template,
            input_text,
            current_prescription,
            additional_info,
            output_summary
        )

        assert prompt_template in result
        assert current_prescription in result
        assert input_text in result
        assert additional_info in result
        assert output_summary in result
        assert '【退院時処方(現在の処方)】' in result
        assert '【カルテ記載】' in result
        assert '【追加情報】' in result
        assert '【生成された出力】' in result

    def test_build_evaluation_prompt_empty_fields(self):
        """空のフィールドを含む評価プロンプト構築のテスト"""
        result = build_evaluation_prompt("テンプレート", "", "", "", "")

        assert "テンプレート" in result
        assert '【前回の記載】' in result
        assert '【カルテ記載】' in result


class TestEvaluateOutputTask:
    """評価タスク実行のテストクラス"""

    @patch('services.evaluation_service.GeminiAPIClient')
    @patch('services.evaluation_service.get_evaluation_prompt')
    @patch('services.evaluation_service.GEMINI_EVALUATION_MODEL', 'gemini-pro')
    def test_evaluate_output_task_success(self, mock_get_prompt, mock_gemini_client):
        """評価タスク成功のテスト"""
        mock_get_prompt.return_value = {
            'content': 'テスト評価プロンプト'
        }

        mock_client_instance = Mock()
        mock_gemini_client.return_value = mock_client_instance
        mock_client_instance.initialize.return_value = True
        mock_client_instance._generate_content.return_value = (
            '評価結果テキスト',
            100,
            200
        )

        result_queue = queue.Queue()

        evaluate_output_task(
            '診療録',
            '前回記載',
            'カルテ記載',
            '追加情報',
            '生成サマリー',
            result_queue
        )

        result = result_queue.get()

        assert result['success'] is True
        assert result['evaluation_result'] == '評価結果テキスト'
        assert result['input_tokens'] == 100
        assert result['output_tokens'] == 200

    @patch('services.evaluation_service.get_evaluation_prompt')
    def test_evaluate_output_task_no_prompt(self, mock_get_prompt):
        """評価プロンプトが存在しない場合のテスト"""
        mock_get_prompt.return_value = None

        result_queue = queue.Queue()

        evaluate_output_task(
            '診療録',
            '前回記載',
            'カルテ記載',
            '追加情報',
            '生成サマリー',
            result_queue
        )

        result = result_queue.get()

        assert result['success'] is False
        assert '評価プロンプトが設定されていません' in result['error']

    @patch('services.evaluation_service.GeminiAPIClient')
    @patch('services.evaluation_service.get_evaluation_prompt')
    @patch('services.evaluation_service.GEMINI_EVALUATION_MODEL', None)
    def test_evaluate_output_task_no_model(self, mock_get_prompt, mock_gemini_client):
        """評価モデルが設定されていない場合のテスト"""
        mock_get_prompt.return_value = {
            'content': 'テスト評価プロンプト'
        }

        result_queue = queue.Queue()

        evaluate_output_task(
            '診療録',
            '前回記載',
            'カルテ記載',
            '追加情報',
            '生成サマリー',
            result_queue
        )

        result = result_queue.get()

        assert result['success'] is False
        assert 'GEMINI_EVALUATION_MODEL' in result['error']

    @patch('services.evaluation_service.GeminiAPIClient')
    @patch('services.evaluation_service.get_evaluation_prompt')
    @patch('services.evaluation_service.GEMINI_EVALUATION_MODEL', 'gemini-pro')
    def test_evaluate_output_task_api_error(self, mock_get_prompt, mock_gemini_client):
        """API呼び出しエラーのテスト"""
        mock_get_prompt.return_value = {
            'content': 'テスト評価プロンプト'
        }

        mock_client_instance = Mock()
        mock_gemini_client.return_value = mock_client_instance
        mock_client_instance.initialize.return_value = True
        mock_client_instance._generate_content.side_effect = Exception("API呼び出しエラー")

        result_queue = queue.Queue()

        evaluate_output_task(
            '診療録',
            '前回記載',
            'カルテ記載',
            '追加情報',
            '生成サマリー',
            result_queue
        )

        result = result_queue.get()

        assert result['success'] is False
        assert 'API呼び出しエラー' in result['error']


class TestDisplayEvaluationProgress:
    """評価進捗表示のテストクラス"""

    @patch('services.evaluation_service.st.spinner')
    @patch('services.evaluation_service.time.sleep')
    def test_display_evaluation_progress(self, mock_sleep, mock_spinner):
        """評価進捗表示のテスト"""
        mock_thread = Mock()
        mock_thread.is_alive.side_effect = [True, True, False]
        mock_placeholder = Mock()
        start_time = datetime.datetime.now()

        mock_spinner_context = MagicMock()
        mock_spinner.return_value.__enter__ = Mock(return_value=mock_spinner_context)
        mock_spinner.return_value.__exit__ = Mock(return_value=False)

        display_evaluation_progress(mock_thread, mock_placeholder, start_time)

        assert mock_sleep.call_count >= 2
        assert mock_placeholder.text.call_count >= 3

    @patch('services.evaluation_service.st.spinner')
    @patch('services.evaluation_service.time.sleep')
    def test_display_evaluation_progress_immediate_completion(self, mock_sleep, mock_spinner):
        """評価がすぐに完了する場合のテスト"""
        mock_thread = Mock()
        mock_thread.is_alive.return_value = False
        mock_placeholder = Mock()
        start_time = datetime.datetime.now()

        mock_spinner_context = MagicMock()
        mock_spinner.return_value.__enter__ = Mock(return_value=mock_spinner_context)
        mock_spinner.return_value.__exit__ = Mock(return_value=False)

        display_evaluation_progress(mock_thread, mock_placeholder, start_time)

        assert mock_placeholder.text.call_count == 1


class TestProcessEvaluation:
    """評価処理メインエントリポイントのテストクラス"""

    @patch('services.evaluation_service.GOOGLE_CREDENTIALS_JSON', None)
    @patch('streamlit.error')
    def test_process_evaluation_no_credentials(self, mock_error):
        """API認証情報が未設定の場合のテスト"""
        mock_placeholder = Mock()

        process_evaluation(
            '診療録',
            '前回記載',
            'カルテ記載',
            '追加情報',
            '生成サマリー',
            mock_placeholder
        )

        mock_error.assert_called()

    @patch('services.evaluation_service.GOOGLE_CREDENTIALS_JSON', 'test_creds')
    @patch('services.evaluation_service.GEMINI_EVALUATION_MODEL', None)
    @patch('streamlit.error')
    def test_process_evaluation_no_model(self, mock_error):
        """評価モデルが未設定の場合のテスト"""
        mock_placeholder = Mock()

        process_evaluation(
            '診療録',
            '前回記載',
            'カルテ記載',
            '追加情報',
            '生成サマリー',
            mock_placeholder
        )

        mock_error.assert_called()

    @patch('services.evaluation_service.GOOGLE_CREDENTIALS_JSON', 'test_creds')
    @patch('services.evaluation_service.GEMINI_EVALUATION_MODEL', 'gemini-pro')
    @patch('streamlit.warning')
    def test_process_evaluation_no_output_summary(self, mock_warning):
        """出力サマリーが空の場合のテスト"""
        mock_placeholder = Mock()

        process_evaluation(
            '診療録',
            '前回記載',
            'カルテ記載',
            '追加情報',
            '',
            mock_placeholder
        )

        mock_warning.assert_called_once()

    @patch('services.evaluation_service.GOOGLE_CREDENTIALS_JSON', 'test_creds')
    @patch('services.evaluation_service.GEMINI_EVALUATION_MODEL', 'gemini-pro')
    @patch('services.evaluation_service.threading.Thread')
    @patch('services.evaluation_service.display_evaluation_progress')
    @patch('streamlit.session_state', create=True)
    @patch('streamlit.spinner')
    def test_process_evaluation_success(
        self,
        mock_spinner,
        mock_session_state,
        mock_display_progress,
        mock_thread
    ):
        """評価処理成功のテスト"""
        mock_placeholder = Mock()
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        mock_thread_instance.is_alive.return_value = False

        result_queue = queue.Queue()
        result_queue.put({
            'success': True,
            'evaluation_result': '評価結果',
            'input_tokens': 100,
            'output_tokens': 200
        })

        with patch('services.evaluation_service.queue.Queue', return_value=result_queue):
            process_evaluation(
                '診療録',
                '前回記載',
                'カルテ記載',
                '追加情報',
                '生成サマリー',
                mock_placeholder
            )

        assert mock_session_state.evaluation_result == '評価結果'
        assert hasattr(mock_session_state, 'evaluation_processing_time')
        assert mock_session_state.evaluation_just_completed is True

    @patch('services.evaluation_service.GOOGLE_CREDENTIALS_JSON', 'test_creds')
    @patch('services.evaluation_service.GEMINI_EVALUATION_MODEL', 'gemini-pro')
    @patch('services.evaluation_service.threading.Thread')
    @patch('services.evaluation_service.display_evaluation_progress')
    @patch('streamlit.error')
    def test_process_evaluation_failure(
        self,
        mock_error,
        mock_display_progress,
        mock_thread
    ):
        """評価処理失敗のテスト"""
        mock_placeholder = Mock()
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        mock_thread_instance.is_alive.return_value = False

        result_queue = queue.Queue()
        result_queue.put({
            'success': False,
            'error': '評価エラー'
        })

        with patch('services.evaluation_service.queue.Queue', return_value=result_queue):
            process_evaluation(
                '診療録',
                '前回記載',
                'カルテ記載',
                '追加情報',
                '生成サマリー',
                mock_placeholder
            )

        mock_error.assert_called()


# フィクスチャーの定義
@pytest.fixture
def sample_evaluation_prompt():
    """テスト用の評価プロンプトデータ"""
    return {
        'document_type': '診療録',
        'content': 'テスト評価プロンプト内容',
        'is_active': True,
        'created_at': datetime.datetime.now(),
        'updated_at': datetime.datetime.now()
    }


@pytest.fixture
def sample_evaluation_result():
    """テスト用の評価結果データ"""
    return {
        'success': True,
        'evaluation_result': '評価結果テキスト',
        'input_tokens': 100,
        'output_tokens': 200
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
