import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from database.db import DatabaseManager
from utils.exceptions import DatabaseError


class TestDatabaseManager:
    """DatabaseManagerクラスのテストクラス"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """各テスト前にシングルトンインスタンスをリセット"""
        DatabaseManager._instance = None
        DatabaseManager._engine = None
        DatabaseManager._session_factory = None
        yield
        # テスト後もクリーンアップ
        DatabaseManager._instance = None
        DatabaseManager._engine = None
        DatabaseManager._session_factory = None

    @pytest.fixture
    def mock_config(self):
        """設定値のモック"""
        with patch.multiple(
                'database.db',
                POSTGRES_HOST='localhost',
                POSTGRES_PORT='5432',
                POSTGRES_USER='testuser',
                POSTGRES_PASSWORD='testpass',
                POSTGRES_DB='testdb',
                POSTGRES_SSL='require'
        ):
            yield

    @pytest.fixture
    def mock_sqlalchemy(self):
        """SQLAlchemyコンポーネントのモック"""
        with patch('database.db.create_engine') as mock_engine, \
                patch('database.db.sessionmaker') as mock_sessionmaker, \
                patch('database.db.text') as mock_text:
            # モックエンジンの設定
            mock_engine_instance = Mock()
            mock_connection = Mock()

            # コンテキストマネージャー用のモック設定
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_connection
            mock_context_manager.__exit__.return_value = None
            mock_engine_instance.connect.return_value = mock_context_manager

            mock_engine.return_value = mock_engine_instance

            # モックセッションファクトリーの設定
            mock_session_factory = Mock()
            mock_sessionmaker.return_value = mock_session_factory

            yield {
                'engine': mock_engine,
                'engine_instance': mock_engine_instance,
                'sessionmaker': mock_sessionmaker,
                'session_factory': mock_session_factory,
                'connection': mock_connection,
                'text': mock_text
            }

    def test_singleton_pattern(self, mock_config, mock_sqlalchemy):
        """シングルトンパターンのテスト"""
        instance1 = DatabaseManager.get_instance()
        instance2 = DatabaseManager.get_instance()

        assert instance1 is instance2
        assert DatabaseManager._instance is not None

    @patch.dict(os.environ, {'DATABASE_URL': 'postgres://user:pass@host:5432/db'})
    def test_init_with_database_url(self, mock_sqlalchemy):
        """DATABASE_URL環境変数を使用した初期化のテスト"""
        DatabaseManager.get_instance()

        # create_engineが正しい接続文字列で呼ばれることを確認
        expected_url = 'postgresql://user:pass@host:5432/db?sslmode=require'
        mock_sqlalchemy['engine'].assert_called_once()
        args, kwargs = mock_sqlalchemy['engine'].call_args
        assert args[0] == expected_url

    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@host:5432/db?option=value'})
    def test_init_with_database_url_with_existing_params(self, mock_sqlalchemy):
        """既存のパラメータがあるDATABASE_URLのテスト"""
        DatabaseManager.get_instance()

        expected_url = 'postgresql://user:pass@host:5432/db?option=value&sslmode=require'
        args, _ = mock_sqlalchemy['engine'].call_args
        assert args[0] == expected_url

    def test_init_with_config_values(self, mock_config, mock_sqlalchemy):
        """設定値を使用した初期化のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            DatabaseManager.get_instance()

            expected_url = 'postgresql://testuser:testpass@localhost:5432/testdb?sslmode=require'
            args, _ = mock_sqlalchemy['engine'].call_args
            assert args[0] == expected_url

    def test_init_missing_config_raises_error(self):
        """設定値が不足している場合のエラーテスト"""
        with patch.dict(os.environ, {}, clear=True), \
                patch('database.db.POSTGRES_HOST', None):
            with pytest.raises(DatabaseError, match="PostgreSQL接続情報が設定されていません"):
                DatabaseManager.get_instance()

    def test_init_database_connection_error(self, mock_config):
        """データベース接続エラーのテスト"""
        with patch('database.db.create_engine') as mock_engine:
            mock_engine.side_effect = SQLAlchemyError("Connection failed")

            with pytest.raises(DatabaseError, match="PostgreSQLへの接続に失敗しました"):
                DatabaseManager.get_instance()

    def test_get_engine(self, mock_config, mock_sqlalchemy):
        """get_engineメソッドのテスト"""
        DatabaseManager.get_instance()
        engine = DatabaseManager.get_engine()

        assert engine == mock_sqlalchemy['engine_instance']

    def test_get_session_before_init_raises_error(self):
        """初期化前のget_session呼び出しエラーテスト"""
        with pytest.raises(DatabaseError, match="データベース接続が初期化されていません"):
            DatabaseManager.get_session()

    def test_get_session(self, mock_config, mock_sqlalchemy):
        """get_sessionメソッドのテスト"""
        DatabaseManager.get_instance()
        session = DatabaseManager.get_session()

        mock_sqlalchemy['session_factory'].assert_called_once()
        assert session == mock_sqlalchemy['session_factory'].return_value


# テスト実行用のconftest.pyファイルに追加する設定例
"""
# conftest.py
import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_database_dependencies():
    \"\"\"テスト実行時にデータベース依存関係をモック化\"\"\"
    with patch('utils.config.POSTGRES_HOST', 'localhost'), \
         patch('utils.config.POSTGRES_PORT', '5432'), \
         patch('utils.config.POSTGRES_USER', 'testuser'), \
         patch('utils.config.POSTGRES_PASSWORD', 'testpass'), \
         patch('utils.config.POSTGRES_DB', 'testdb'), \
         patch('utils.config.POSTGRES_SSL', 'require'):
        yield
"""