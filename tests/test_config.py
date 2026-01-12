import os
from pathlib import Path
from unittest.mock import patch, Mock

# テスト対象のモジュールをインポート
from utils.config import (
    get_config,
    parse_database_url
)


class TestGetConfig:
    """get_config関数のテスト"""
    
    @patch('utils.config.Path')
    @patch('configparser.ConfigParser')
    def test_get_config_success(self, mock_configparser, mock_path):
        """設定ファイルの正常読み込みテスト"""
        # モックの設定
        mock_config = Mock()
        mock_configparser.return_value = mock_config
        mock_path.return_value.parent.parent = Path('/test/base')

        with patch('os.path.join', return_value='/test/base/utils/config.ini'):
            result = get_config()

        # 検証
        mock_config.read.assert_called_once_with('/test/base/utils/config.ini', encoding='utf-8')
        assert result == mock_config
    
    @patch('utils.config.Path')
    @patch('configparser.ConfigParser')
    def test_get_config_file_not_found(self, mock_configparser, mock_path):
        """設定ファイルが見つからない場合のテスト"""
        mock_config = Mock()
        mock_configparser.return_value = mock_config
        mock_path.return_value.parent.parent = Path('/test/base')

        # ファイルが存在しない場合でもConfigParserは例外を投げないため、
        # 正常に動作することを確認
        with patch('os.path.join', return_value='/nonexistent/utils/config.ini'):
            result = get_config()

        assert result == mock_config


class TestParseDatabaseUrl:
    """parse_database_url関数のテスト"""
    
    def test_parse_database_url_with_valid_url(self):
        """有効なDATABASE_URLの解析テスト"""
        test_url = "postgresql://user:password@localhost:5432/dbname"
        
        with patch.dict(os.environ, {'DATABASE_URL': test_url}):
            result = parse_database_url()
            
        expected = {
            "host": "localhost",
            "port": 5432,
            "user": "user",
            "password": "password",
            "database": "dbname"
        }
        assert result == expected
    
    def test_parse_database_url_with_no_url(self):
        """DATABASE_URLが設定されていない場合のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            result = parse_database_url()
            
        assert result is None
    
    def test_parse_database_url_with_empty_url(self):
        """空のDATABASE_URLの場合のテスト"""
        with patch.dict(os.environ, {'DATABASE_URL': ''}):
            result = parse_database_url()
            
        assert result is None
    
    def test_parse_database_url_with_complex_password(self):
        """特殊文字を含むパスワードのテスト"""
        test_url = "postgresql://user:p%40ssw0rd@localhost:5432/dbname"
        
        with patch.dict(os.environ, {'DATABASE_URL': test_url}):
            result = parse_database_url()
            
        assert result["password"] == "p%40ssw0rd"
    
    def test_parse_database_url_with_different_scheme(self):
        """PostgreSQL以外のスキームのテスト"""
        test_url = "mysql://user:password@localhost:3306/dbname"
        
        with patch.dict(os.environ, {'DATABASE_URL': test_url}):
            result = parse_database_url()
            
        expected = {
            "host": "localhost",
            "port": 3306,
            "user": "user",
            "password": "password",
            "database": "dbname"
        }
        assert result == expected


class TestEnvironmentVariables:
    """環境変数の設定テスト"""
    
    def test_postgres_config_from_database_url(self):
        """DATABASE_URLから設定が読み込まれることのテスト"""
        test_url = "postgresql://testuser:testpass@testhost:9999/testdb"
        
        with patch.dict(os.environ, {'DATABASE_URL': test_url}):
            # モジュールを再インポートして環境変数を再評価
            import importlib
            import utils.config
            importlib.reload(utils.config)
            
            assert utils.config.POSTGRES_HOST == "testhost"
            assert utils.config.POSTGRES_PORT == 9999
            assert utils.config.POSTGRES_USER == "testuser"
            assert utils.config.POSTGRES_PASSWORD == "testpass"
            assert utils.config.POSTGRES_DB == "testdb"
            assert utils.config.POSTGRES_SSL == "require"
    
    def test_ai_model_config(self):
        """AIモデル関連の設定テスト"""
        env_vars = {
            'GOOGLE_CREDENTIALS_JSON': 'test_gemini_creds',
            'GEMINI_MODEL': 'gemini-pro',
            'AWS_ACCESS_KEY_ID': 'test_access_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret_key',
            'AWS_REGION': 'us-east-1',
            'ANTHROPIC_MODEL': 'claude-3-sonnet',
            'SELECTED_AI_MODEL': 'claude'
        }

        with patch.dict(os.environ, env_vars):
            import importlib
            import utils.config
            importlib.reload(utils.config)

            assert utils.config.GOOGLE_CREDENTIALS_JSON == 'test_gemini_creds'
            assert utils.config.GEMINI_MODEL == 'gemini-pro'
            assert utils.config.CLAUDE_API_KEY == True  # AWS設定があればTrue
            assert utils.config.ANTHROPIC_MODEL == 'claude-3-sonnet'
            assert utils.config.SELECTED_AI_MODEL == 'claude'
    
    def test_token_limits_config(self):
        """トークン制限の設定テスト"""
        env_vars = {
            'MAX_INPUT_TOKENS': '300000',
            'MIN_INPUT_TOKENS': '200',
            'MAX_TOKEN_THRESHOLD': '50000'
        }
        
        with patch.dict(os.environ, env_vars):
            import importlib
            import utils.config
            importlib.reload(utils.config)
            
            assert utils.config.MAX_INPUT_TOKENS == 300000
            assert utils.config.MIN_INPUT_TOKENS == 200
            assert utils.config.MAX_TOKEN_THRESHOLD == 50000
