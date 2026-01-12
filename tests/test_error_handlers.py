from unittest.mock import patch

from utils.error_handlers import handle_error
from utils.exceptions import AppError, APIError, DatabaseError


class TestHandleErrorDecorator:
    """handle_errorデコレータのテスト"""
    
    @patch('streamlit.error')
    def test_handle_api_error(self, mock_st_error):
        """APIErrorのハンドリングテスト"""
        @handle_error
        def test_func():
            raise APIError("API接続に失敗しました")
        
        result = test_func()
        
        # Noneが返されることを確認
        assert result is None
        # streamlit.errorが正しいメッセージで呼ばれることを確認
        mock_st_error.assert_called_once_with("API接続エラー: API接続に失敗しました")
    
    @patch('streamlit.error')
    def test_handle_database_error(self, mock_st_error):
        """DatabaseErrorのハンドリングテスト"""
        @handle_error
        def test_func():
            raise DatabaseError("データベース接続に失敗しました")
        
        result = test_func()
        
        assert result is None
        mock_st_error.assert_called_once_with("データベースエラー: データベース接続に失敗しました")
    
    @patch('streamlit.error')
    def test_handle_app_error(self, mock_st_error):
        """AppErrorのハンドリングテスト"""
        @handle_error
        def test_func():
            raise AppError("アプリケーションエラーが発生しました")
        
        result = test_func()
        
        assert result is None
        mock_st_error.assert_called_once_with("エラーが発生しました: アプリケーションエラーが発生しました")
    
    @patch('streamlit.error')
    def test_handle_generic_exception(self, mock_st_error):
        """一般的な例外のハンドリングテスト"""
        @handle_error
        def test_func():
            raise ValueError("予期しない値エラー")
        
        result = test_func()
        
        assert result is None
        mock_st_error.assert_called_once_with("予期しないエラー: 予期しない値エラー")
    
    @patch('streamlit.error')
    def test_no_error_normal_execution(self, mock_st_error):
        """正常実行時のテスト"""
        @handle_error
        def test_func():
            return "成功"
        
        result = test_func()
        
        # 正常な戻り値が返されることを確認
        assert result == "成功"
        # streamlit.errorが呼ばれないことを確認
        mock_st_error.assert_not_called()
    
    @patch('streamlit.error')
    def test_function_with_arguments(self, mock_st_error):
        """引数がある関数のテスト"""
        @handle_error
        def test_func(arg1, arg2, kwarg1=None):
            if arg1 == "error":
                raise APIError("引数エラー")
            return f"{arg1}_{arg2}_{kwarg1}"
        
        # 正常ケース
        result = test_func("hello", "world", kwarg1="test")
        assert result == "hello_world_test"
        mock_st_error.assert_not_called()
        
        # エラーケース
        result = test_func("error", "world", kwarg1="test")
        assert result is None
        mock_st_error.assert_called_once_with("API接続エラー: 引数エラー")
    
    @patch('streamlit.error')
    def test_nested_exceptions(self, mock_st_error):
        """ネストした例外のテスト"""
        @handle_error
        def test_func():
            try:
                raise ValueError("内部エラー")
            except ValueError as e:
                raise DatabaseError(f"データベースエラー: {str(e)}")
        
        result = test_func()
        
        assert result is None
        mock_st_error.assert_called_once_with("データベースエラー: データベースエラー: 内部エラー")
    
    @patch('streamlit.error')
    def test_empty_error_message(self, mock_st_error):
        """空のエラーメッセージのテスト"""
        @handle_error
        def test_func():
            raise APIError("")
        
        result = test_func()
        
        assert result is None
        mock_st_error.assert_called_once_with("API接続エラー: ")
    
    @patch('streamlit.error')
    def test_unicode_error_message(self, mock_st_error):
        """Unicode文字を含むエラーメッセージのテスト"""
        @handle_error
        def test_func():
            raise AppError("日本語エラーメッセージ: 😀")
        
        result = test_func()
        
        assert result is None
        mock_st_error.assert_called_once_with("エラーが発生しました: 日本語エラーメッセージ: 😀")
    
    @patch('streamlit.error')
    def test_multiple_function_calls(self, mock_st_error):
        """複数回の関数呼び出しテスト"""
        @handle_error
        def test_func(should_error=False):
            if should_error:
                raise APIError("テストエラー")
            return "OK"
        
        # 1回目: 正常
        result1 = test_func()
        assert result1 == "OK"
        
        # 2回目: エラー
        result2 = test_func(True)
        assert result2 is None
        
        # 3回目: 正常
        result3 = test_func()
        assert result3 == "OK"
        
        # エラーメッセージが1回だけ表示されることを確認
        mock_st_error.assert_called_once_with("API接続エラー: テストエラー")
