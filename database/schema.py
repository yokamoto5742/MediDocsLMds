import os
import time
from subprocess import PIPE, run

from database.db import DatabaseManager
from database.models import Base
from utils.constants import MESSAGES
from utils.exceptions import DatabaseError


def run_alembic_migrations():
    """Alembicマイグレーションを実行する"""
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        result = run(
            ["alembic", "upgrade", "head"],
            cwd=root_dir,
            stdout=PIPE,
            stderr=PIPE,
            text=True
        )

        if result.returncode != 0:
            print(f"警告: マイグレーション実行中にエラーが発生しました: {result.stderr}")
            return False

        print("データベースマイグレーションが正常に完了しました。")
        return True
    except Exception as e:
        print(f"マイグレーション実行中にエラーが発生しました: {str(e)}")
        return False


def create_tables():
    """ORMモデルからテーブルを作成する"""
    try:
        db_manager = DatabaseManager.get_instance()
        engine = db_manager.get_engine()
        Base.metadata.create_all(engine)
        return True
    except Exception as e:
        raise DatabaseError(MESSAGES["DATABASE_TABLE_CREATE_ERROR"].format(error=str(e)))


def initialize_database():
    """データベースを初期化する（リトライロジック付き）"""
    max_retries = 5
    retry_count = 0
    last_error = None

    while retry_count < max_retries:
        try:
            create_tables()
            return True
        except Exception as e:
            last_error = e
            retry_count += 1
            wait_time = 2 ** retry_count  # 指数バックオフ
            print(f"データベース初期化に失敗しました（試行 {retry_count}/{max_retries}）: {str(e)}")
            print(f"{wait_time}秒後に再試行します...")
            time.sleep(wait_time)

    raise DatabaseError(MESSAGES["DATABASE_INIT_FAILED"].format(error=str(last_error)))
