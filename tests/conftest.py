import os
import shutil
import pytest
import logging
import tempfile
from unittest.mock import Mock


@pytest.fixture(scope="session", autouse=True)
def cleanup_magicmock_dirs(request):
    yield

    root_dir = os.path.dirname(os.path.dirname(__file__))

    magicmock_dirs = [
        os.path.join(os.path.dirname(__file__), "MagicMock"),
        os.path.join(root_dir, "MagicMock")
    ]

    for magicmock_dir in magicmock_dirs:
        if os.path.exists(magicmock_dir):
            print(f"\nクリーンアップ: {magicmock_dir} を削除します")
            try:
                shutil.rmtree(magicmock_dir)
                print(f"{magicmock_dir} の削除に成功しました")
            except Exception as e:
                print(f"{magicmock_dir} の削除中にエラーが発生しました: {e}")


@pytest.fixture(autouse=True)
def suppress_streamlit_warnings():
    logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)
    logging.getLogger("streamlit.runtime.state.session_state_proxy").setLevel(logging.ERROR)
    logging.getLogger("streamlit").setLevel(logging.ERROR)


@pytest.fixture
def temp_config_file():
    """テスト用の一時的なconfig.iniファイル"""
    content = """
[PROMPTS]
summary = これはテスト用のプロンプトです。患者の退院サマリーを作成してください。

[DATABASE]
host = localhost
port = 5432
name = test_db
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False, encoding='utf-8') as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_env_file():
    """テスト用の一時的な.envファイル"""
    content = """
DATABASE_URL=postgresql://user:pass@localhost:5432/testdb
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=testuser
POSTGRES_PASSWORD=testpass
POSTGRES_DB=testdb
GOOGLE_CREDENTIALS_JSON=test_credentials
CLAUDE_API_KEY=test_claude_key
OPENAI_API_KEY=test_openai_key
SELECTED_AI_MODEL=gemini
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def mock_database_manager():
    """モックデータベースマネージャー"""
    mock = Mock()
    mock.execute_query.return_value = []
    mock.get_session.return_value = Mock()
    return mock


@pytest.fixture
def sample_prompt_data():
    """テスト用のプロンプトデータ"""
    return {
        "department": "内科",
        "document_type": "主治医意見書",
        "doctor": "田中医師",
        "content": "テスト用のプロンプト内容",
        "selected_model": "gemini",
        "is_default": False
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """各テスト前後で環境変数をリセット"""
    original_env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(original_env)
