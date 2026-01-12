import datetime
from unittest.mock import Mock, patch

import pytest

from utils.exceptions import DatabaseError
from utils.prompt_manager import (
    create_or_update_prompt,
    delete_prompt,
    get_all_departments,
    get_all_prompts,
    get_current_datetime,
    get_prompt,
    initialize_database,
    initialize_default_prompt,
)


class TestGetCurrentDatetime:
    """get_current_datetime関数のテスト"""
    
    def test_get_current_datetime(self):
        """現在時刻の取得テスト"""
        with patch('utils.prompt_manager.datetime') as mock_datetime:
            mock_now = datetime.datetime(2024, 1, 1, 12)
            mock_datetime.datetime.now.return_value = mock_now
            
            result = get_current_datetime()
            
            assert result == mock_now
            mock_datetime.datetime.now.assert_called_once()


class TestGetAllDepartments:
    """get_all_departments関数のテスト"""
    
    @patch('utils.prompt_manager.DEFAULT_DEPARTMENT', ['内科', '外科', '小児科'])
    def test_get_all_departments(self):
        """全部署の取得テスト"""
        result = get_all_departments()
        assert result == ['内科', '外科', '小児科']


class TestGetAllPrompts:
    """get_all_prompts関数のテスト"""

    def test_get_all_prompts_success(self, mock_database_manager):
        """プロンプト一覧の正常取得テスト"""
        from database.models import Prompt
        expected_prompts = [
            {"department": "内科", "content": "内科用プロンプト"},
            {"department": "外科", "content": "外科用プロンプト"}
        ]
        mock_database_manager.query_all.return_value = expected_prompts

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            result = get_all_prompts()

            assert result == expected_prompts
            mock_database_manager.query_all.assert_called_once_with(Prompt, order_by=Prompt.department)

    def test_get_all_prompts_database_error(self, mock_database_manager):
        """データベースエラーのテスト"""
        mock_database_manager.query_all.side_effect = Exception("DB接続エラー")

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            with pytest.raises(DatabaseError, match="プロンプト一覧の取得に失敗しました"):
                get_all_prompts()


class TestCreateOrUpdatePrompt:
    """create_or_update_prompt関数のテスト"""

    def test_create_or_update_prompt_update_existing(self, mock_database_manager):
        """既存プロンプトの更新テスト"""
        # 既存のプロンプトが存在する場合
        existing_prompt = {"id": 1, "content": "既存プロンプト"}
        mock_database_manager.query_one.return_value = existing_prompt
        mock_database_manager.update.return_value = {"id": 1, "content": "新しいプロンプト"}

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            success, message = create_or_update_prompt(
                "内科", "主治医意見書", "田中医師", "新しいプロンプト", "gemini"
            )

            assert success is True
            assert message == "プロンプトを更新しました"
            mock_database_manager.query_one.assert_called_once()
            mock_database_manager.update.assert_called_once()

    def test_create_or_update_prompt_create_new(self, mock_database_manager):
        """新規プロンプトの作成テスト"""
        # 既存のプロンプトが存在しない場合
        mock_database_manager.query_one.return_value = None
        mock_database_manager.insert.return_value = {"id": 1}

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            with patch('utils.prompt_manager.get_current_datetime') as mock_datetime:
                mock_now = datetime.datetime(2024, 1, 1, 12)
                mock_datetime.return_value = mock_now

                success, message = create_or_update_prompt(
                    "内科", "主治医意見書", "田中医師", "新しいプロンプト", "gemini"
                )

                assert success is True
                assert message == "プロンプトを新規作成しました"
                mock_database_manager.insert.assert_called_once()

    def test_create_or_update_prompt_invalid_input(self):
        """無効な入力のテスト"""
        success, message = create_or_update_prompt("", "", "", "")

        assert success is False
        assert message == "すべての項目を入力してください"

    def test_create_or_update_prompt_database_error(self, mock_database_manager):
        """データベースエラーのテスト"""
        mock_database_manager.query_one.side_effect = DatabaseError("DB接続エラー")

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            success, message = create_or_update_prompt(
                "内科", "主治医意見書", "田中医師", "新しいプロンプト"
            )

            assert success is False
            assert "DB接続エラー" in message


class TestDeletePrompt:
    """delete_prompt関数のテスト"""

    def test_delete_prompt_success(self, mock_database_manager):
        """プロンプト削除の成功テスト"""
        from database.models import Prompt
        mock_database_manager.delete.return_value = True

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            success, message = delete_prompt("内科", "主治医意見書", "田中医師")

            assert success is True
            assert message == "プロンプトを削除しました"
            mock_database_manager.delete.assert_called_once_with(
                Prompt,
                {"department": "内科", "document_type": "主治医意見書", "doctor": "田中医師"}
            )

    def test_delete_prompt_default_protection(self):
        """デフォルトプロンプトの削除保護テスト"""
        success, message = delete_prompt("default", "主治医意見書", "default")

        assert success is False
        assert message == "デフォルトプロンプトは削除できません"

    def test_delete_prompt_not_found(self, mock_database_manager):
        """存在しないプロンプトの削除テスト"""
        mock_database_manager.delete.return_value = False

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            success, message = delete_prompt("内科", "主治医意見書", "田中医師")

            assert success is False
            assert message == "プロンプトが見つかりません"

    def test_delete_prompt_database_error(self, mock_database_manager):
        """データベースエラーのテスト"""
        mock_database_manager.delete.side_effect = DatabaseError("DB接続エラー")

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            success, message = delete_prompt("内科", "主治医意見書", "田中医師")

            assert success is False
            assert "DB接続エラー" in message


class TestGetPrompt:
    """get_prompt関数のテスト"""

    def test_get_prompt_found(self, mock_database_manager):
        """プロンプトが見つかった場合のテスト"""
        expected_prompt = {
            "id": 1,
            "department": "内科",
            "document_type": "主治医意見書",
            "doctor": "田中医師",
            "content": "内科用プロンプト"
        }
        mock_database_manager.query_one.return_value = expected_prompt

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            result = get_prompt("内科", "主治医意見書", "田中医師")

            assert result == expected_prompt
            mock_database_manager.query_one.assert_called_once()

    def test_get_prompt_fallback_to_default(self, mock_database_manager):
        """デフォルトプロンプトにフォールバックするテスト"""
        default_prompt = {
            "id": 1,
            "department": "default",
            "document_type": "主治医意見書",
            "doctor": "default",
            "content": "デフォルトプロンプト"
        }

        # 最初のクエリはNone、2番目のクエリでデフォルトを返す
        mock_database_manager.query_one.side_effect = [None, default_prompt]

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            with patch('utils.prompt_manager.DEFAULT_DOCUMENT_TYPE', '主治医意見書'):
                result = get_prompt("存在しない部署", "主治医意見書", "存在しない医師")

                assert result == default_prompt
                assert mock_database_manager.query_one.call_count == 2

    def test_get_prompt_no_default_found(self, mock_database_manager):
        """デフォルトプロンプトも見つからない場合のテスト"""
        mock_database_manager.query_one.return_value = None

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            result = get_prompt("存在しない部署", "存在しない文書", "存在しない医師")

            assert result is None

    def test_get_prompt_database_error(self, mock_database_manager):
        """データベースエラーのテスト"""
        mock_database_manager.query_one.side_effect = Exception("DB接続エラー")

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            with pytest.raises(DatabaseError, match="プロンプトの取得に失敗しました"):
                get_prompt("内科", "主治医意見書", "田中医師")


class TestInitializeDefaultPrompt:
    """initialize_default_prompt関数のテスト"""

    def test_initialize_default_prompt_not_exists(self, mock_database_manager):
        """デフォルトプロンプトが存在しない場合のテスト"""
        # デフォルトプロンプトが存在しない
        mock_database_manager.query_one.return_value = None
        mock_database_manager.insert.return_value = {"id": 1}

        mock_config = Mock()
        mock_config.__getitem__ = Mock(return_value={'summary': 'デフォルトプロンプト内容'})

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            with patch('utils.prompt_manager.get_config', return_value=mock_config):
                with patch('utils.prompt_manager.get_current_datetime') as mock_datetime:
                    with patch('utils.prompt_manager.DEFAULT_DOCUMENT_TYPE', '主治医意見書'):
                        mock_now = datetime.datetime(2024, 1, 1, 12)
                        mock_datetime.return_value = mock_now

                        initialize_default_prompt()

                        mock_database_manager.insert.assert_called_once()
                        insert_args = mock_database_manager.insert.call_args[0][1]
                        assert insert_args['department'] == 'default'
                        assert insert_args['document_type'] == '主治医意見書'
                        assert insert_args['doctor'] == 'default'
                        assert insert_args['is_default'] is True

    def test_initialize_default_prompt_already_exists(self, mock_database_manager):
        """デフォルトプロンプトが既に存在する場合のテスト"""
        existing_prompt = {"id": 1, "content": "既存プロンプト"}
        mock_database_manager.query_one.return_value = existing_prompt

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            with patch('utils.prompt_manager.DEFAULT_DOCUMENT_TYPE', '主治医意見書'):
                initialize_default_prompt()

                # insertが呼ばれないことを確認
                mock_database_manager.insert.assert_not_called()

    def test_initialize_default_prompt_error(self, mock_database_manager):
        """初期化中にエラーが発生した場合のテスト"""
        mock_database_manager.query_one.side_effect = Exception("DB接続エラー")

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            with pytest.raises(DatabaseError, match="デフォルトプロンプトの初期化に失敗しました"):
                initialize_default_prompt()


class TestInitializeDatabase:
    """initialize_database関数のテスト"""

    @patch('utils.prompt_manager.init_schema')
    @patch('utils.prompt_manager.initialize_default_prompt')
    def test_initialize_database_success(self, mock_init_default, mock_init_schema, mock_database_manager):
        """データベース初期化の成功テスト"""
        mock_config = Mock()
        mock_config.__getitem__ = Mock(return_value={'summary': 'デフォルトプロンプト内容'})

        # 既存プロンプトが存在しない場合をシミュレート
        mock_database_manager.query_one.return_value = None
        mock_database_manager.insert.return_value = {"id": 1}

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            with patch('utils.prompt_manager.get_config', return_value=mock_config):
                with patch('utils.prompt_manager.DEFAULT_DEPARTMENT', ['内科']):
                    with patch('utils.prompt_manager.DOCUMENT_TYPES', ['主治医意見書']):
                        with patch('utils.prompt_manager.DEPARTMENT_DOCTORS_MAPPING', {'内科': ['田中医師']}):
                            with patch('utils.prompt_manager.get_current_datetime') as mock_datetime:
                                mock_now = datetime.datetime(2024, 1, 1, 12)
                                mock_datetime.return_value = mock_now

                                initialize_database()

                                # スキーマ初期化とデフォルトプロンプト初期化が呼ばれることを確認
                                mock_init_schema.assert_called_once()
                                mock_init_default.assert_called_once()

                                # 新しいプロンプトが挿入されることを確認
                                mock_database_manager.insert.assert_called()

    @patch('utils.prompt_manager.init_schema')
    @patch('utils.prompt_manager.initialize_default_prompt')
    def test_initialize_database_existing_prompts(self, mock_init_default, mock_init_schema, mock_database_manager):
        """既存プロンプトがある場合のテスト"""
        # 既存プロンプトが存在する場合をシミュレート
        existing_prompt = {"id": 1, "content": "既存プロンプト"}
        mock_database_manager.query_one.return_value = existing_prompt

        with patch('utils.prompt_manager.get_db_manager', return_value=mock_database_manager):
            with patch('utils.prompt_manager.DEFAULT_DEPARTMENT', ['内科']):
                with patch('utils.prompt_manager.DOCUMENT_TYPES', ['主治医意見書']):
                    with patch('utils.prompt_manager.DEPARTMENT_DOCTORS_MAPPING', {'内科': ['田中医師']}):
                        initialize_database()

                        # 既存プロンプトがあるため、新しい挿入は行われない
                        mock_database_manager.insert.assert_not_called()

    @patch('utils.prompt_manager.init_schema')
    def test_initialize_database_error(self, mock_init_schema):
        """初期化中にエラーが発生した場合のテスト"""
        mock_init_schema.side_effect = Exception("スキーマ初期化エラー")

        with pytest.raises(DatabaseError, match="データベースの初期化に失敗しました"):
            initialize_database()
