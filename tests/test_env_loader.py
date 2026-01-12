import os
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.env_loader import load_environment_variables


class TestLoadEnvironmentVariables:
    """load_environment_variables関数のテスト"""
    
    @patch('utils.env_loader.load_dotenv')
    @patch('utils.env_loader.os.path.exists')
    @patch('utils.env_loader.os.path.join')
    @patch('utils.env_loader.Path')
    @patch('builtins.print')
    def test_load_env_file_exists(self, mock_print, mock_path, mock_join, mock_exists, mock_load_dotenv):
        """環境ファイルが存在する場合のテスト"""
        # モックの設定
        mock_path.return_value.parent.parent = Path('/test/base')
        mock_join.return_value = '/test/base/.env'
        mock_exists.return_value = True
        
        # テスト実行
        load_environment_variables()
        
        # 検証
        mock_join.assert_called_once_with(Path('/test/base'), '.env')
        mock_exists.assert_called_once_with('/test/base/.env')
        mock_load_dotenv.assert_called_once_with('/test/base/.env')
        mock_print.assert_called_once_with("環境変数を.envファイルから読み込みました")
    
    @patch('utils.env_loader.load_dotenv')
    @patch('utils.env_loader.os.path.exists')
    @patch('utils.env_loader.os.path.join')
    @patch('utils.env_loader.Path')
    @patch('builtins.print')
    def test_load_env_file_not_exists(self, mock_print, mock_path, mock_join, mock_exists, mock_load_dotenv):
        """環境ファイルが存在しない場合のテスト"""
        # モックの設定
        mock_path.return_value.parent.parent = Path('/test/base')
        mock_join.return_value = '/test/base/.env'
        mock_exists.return_value = False
        
        # テスト実行
        load_environment_variables()
        
        # 検証
        mock_join.assert_called_once_with(Path('/test/base'), '.env')
        mock_exists.assert_called_once_with('/test/base/.env')
        mock_load_dotenv.assert_not_called()
        mock_print.assert_called_once_with("警告: .envファイルが見つかりません。システム環境変数が設定されていることを確認してください。")
    
    @patch('utils.env_loader.load_dotenv')
    @patch('utils.env_loader.os.path.exists')
    @patch('utils.env_loader.os.path.join')
    @patch('utils.env_loader.Path')
    def test_load_env_path_construction(self, mock_path, mock_join, mock_exists, mock_load_dotenv):
        """パス構築が正しく行われることのテスト"""
        # テスト用のパスを設定
        test_base_dir = Path('/project/root')
        mock_path.return_value.parent.parent = test_base_dir
        mock_exists.return_value = True
        
        # テスト実行
        load_environment_variables()
        
        # パスの構築が正しく行われることを確認
        mock_join.assert_called_once_with(test_base_dir, '.env')
    
    @patch('utils.env_loader.load_dotenv')
    @patch('utils.env_loader.os.path.exists')
    @patch('utils.env_loader.os.path.join')
    @patch('utils.env_loader.Path')
    def test_load_env_exception_handling(self, mock_path, mock_join, mock_exists, mock_load_dotenv):
        """例外が発生した場合のテスト"""
        # モックの設定
        mock_path.return_value.parent.parent = Path('/test/base')
        mock_join.return_value = '/test/base/.env'
        mock_exists.return_value = True
        mock_load_dotenv.side_effect = Exception("テスト例外")
        
        # 例外が発生することを確認
        with pytest.raises(Exception, match="テスト例外"):
            load_environment_variables()
    
    def test_integration_with_real_file(self, temp_env_file):
        """実際のファイルを使用した統合テスト"""
        # 一時ファイルのディレクトリを取得
        env_dir = os.path.dirname(temp_env_file)
        env_filename = os.path.basename(temp_env_file)
        
        with patch('utils.env_loader.Path') as mock_path:
            mock_path.return_value.parent.parent = Path(env_dir)
            
            with patch('utils.env_loader.os.path.join') as mock_join:
                mock_join.return_value = temp_env_file
                
                with patch('builtins.print') as mock_print:
                    # テスト実行
                    load_environment_variables()
                    
                    # 正常メッセージが出力されることを確認
                    mock_print.assert_called_once_with("環境変数を.envファイルから読み込みました")
