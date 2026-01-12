import os
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from database.models import Base
from utils.config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_SSL,
    POSTGRES_USER,
)
from utils.constants import MESSAGES
from utils.exceptions import DatabaseError


class DatabaseManager:
    _instance = None
    _engine = None
    _session_factory = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance

    def __init__(self):
        if DatabaseManager._engine is not None:
            return

        database_url = os.environ.get("DATABASE_URL")

        if database_url:
            try:
                if database_url.startswith("postgres://"):
                    database_url = database_url.replace("postgres://", "postgresql://", 1)

                if "?" in database_url:
                    database_url += "&sslmode=require"
                else:
                    database_url += "?sslmode=require"

                connection_string = database_url

            except Exception as e:
                raise DatabaseError(MESSAGES["DATABASE_URL_PARSE_ERROR"].format(error=str(e)))
        else:
            if not all([POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
                raise DatabaseError(MESSAGES["DATABASE_CONNECTION_INFO_MISSING"])

            connection_string = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

            if POSTGRES_SSL:
                connection_string += f"?sslmode={POSTGRES_SSL}"

        try:
            DatabaseManager._engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600
            )

            DatabaseManager._session_factory = sessionmaker(bind=DatabaseManager._engine)

            with DatabaseManager._engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        except Exception as e:
            raise DatabaseError(MESSAGES["DATABASE_CONNECTION_ERROR"].format(error=str(e)))

    @staticmethod
    def get_engine():
        return DatabaseManager._engine

    @staticmethod
    def get_session():
        if DatabaseManager._session_factory is None:
            raise DatabaseError(MESSAGES["DATABASE_NOT_INITIALIZED"])
        return DatabaseManager._session_factory()

    def query_all(self, model_class: Type[Base], filters: Optional[Dict[str, Any]] = None,
                  order_by: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        ORMを使用して全レコードを取得する

        Args:
            model_class: クエリ対象のモデルクラス
            filters: フィルタ条件の辞書
            order_by: ソート条件

        Returns:
            辞書形式のレコードリスト
        """
        session = self.get_session()
        try:
            query = session.query(model_class)

            if filters:
                for key, value in filters.items():
                    if hasattr(model_class, key):
                        query = query.filter(getattr(model_class, key) == value)

            if order_by is not None:
                query = query.order_by(order_by)

            results = query.all()
            return [self._model_to_dict(record) for record in results]

        except Exception as e:
            session.rollback()
            raise DatabaseError(MESSAGES["DATABASE_QUERY_ERROR"].format(error=str(e)))
        finally:
            session.close()

    def query_one(self, model_class: Type[Base], filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        ORMを使用して1レコードを取得する

        Args:
            model_class: クエリ対象のモデルクラス
            filters: フィルタ条件の辞書

        Returns:
            辞書形式のレコード、見つからない場合はNone
        """
        session = self.get_session()
        try:
            query = session.query(model_class)

            for key, value in filters.items():
                if hasattr(model_class, key):
                    query = query.filter(getattr(model_class, key) == value)

            record = query.first()
            return self._model_to_dict(record) if record else None

        except Exception as e:
            session.rollback()
            raise DatabaseError(MESSAGES["DATABASE_QUERY_ERROR"].format(error=str(e)))
        finally:
            session.close()

    def get_by_id(self, model_class: Type[Base], record_id: int) -> Optional[Dict[str, Any]]:
        """
        IDでレコードを取得する

        Args:
            model_class: クエリ対象のモデルクラス
            record_id: 取得するレコードのID

        Returns:
            辞書形式のレコード、見つからない場合はNone
        """
        session = self.get_session()
        try:
            record = session.get(model_class, record_id)
            return self._model_to_dict(record) if record else None

        except Exception as e:
            session.rollback()
            raise DatabaseError(MESSAGES["DATABASE_GET_RECORD_ERROR"].format(error=str(e)))
        finally:
            session.close()

    def insert(self, model_class: Type[Base], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レコードを挿入する

        Args:
            model_class: 挿入対象のモデルクラス
            data: 挿入するデータの辞書

        Returns:
            挿入されたレコードの辞書形式
        """
        session = self.get_session()
        try:
            record = model_class(**data)
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._model_to_dict(record)

        except Exception as e:
            session.rollback()
            raise DatabaseError(MESSAGES["DATABASE_INSERT_ERROR"].format(error=str(e)))
        finally:
            session.close()

    def update(self, model_class: Type[Base], filters: Dict[str, Any],
               update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        レコードを更新する

        Args:
            model_class: 更新対象のモデルクラス
            filters: 検索条件の辞書
            update_data: 更新データの辞書

        Returns:
            更新されたレコードの辞書形式、見つからない場合はNone
        """
        session = self.get_session()
        try:
            query = session.query(model_class)

            for key, value in filters.items():
                if hasattr(model_class, key):
                    query = query.filter(getattr(model_class, key) == value)

            record = query.first()
            if record is None:
                return None

            for key, value in update_data.items():
                if hasattr(record, key):
                    setattr(record, key, value)

            session.commit()
            session.refresh(record)
            return self._model_to_dict(record)

        except Exception as e:
            session.rollback()
            raise DatabaseError(MESSAGES["DATABASE_UPDATE_ERROR"].format(error=str(e)))
        finally:
            session.close()

    def upsert(self, model_class: Type[Base], filters: Dict[str, Any],
               data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レコードを挿入または更新する

        Args:
            model_class: 対象のモデルクラス
            filters: 検索条件の辞書
            data: 挿入/更新するデータの辞書

        Returns:
            挿入/更新されたレコードの辞書形式
        """
        session = self.get_session()
        try:
            query = session.query(model_class)

            for key, value in filters.items():
                if hasattr(model_class, key):
                    query = query.filter(getattr(model_class, key) == value)

            record = query.first()

            if record:
                for key, value in data.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
            else:
                merged_data = {**filters, **data}
                record = model_class(**merged_data)
                session.add(record)

            session.commit()
            session.refresh(record)
            return self._model_to_dict(record)

        except Exception as e:
            session.rollback()
            raise DatabaseError(MESSAGES["DATABASE_UPSERT_ERROR"].format(error=str(e)))
        finally:
            session.close()

    def delete(self, model_class: Type[Base], filters: Dict[str, Any]) -> bool:
        """
        レコードを削除する

        Args:
            model_class: 削除対象のモデルクラス
            filters: 検索条件の辞書

        Returns:
            削除成功時はTrue、見つからない場合はFalse
        """
        session = self.get_session()
        try:
            query = session.query(model_class)

            for key, value in filters.items():
                if hasattr(model_class, key):
                    query = query.filter(getattr(model_class, key) == value)

            record = query.first()
            if record is None:
                return False

            session.delete(record)
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise DatabaseError(MESSAGES["DATABASE_DELETE_ERROR"].format(error=str(e)))
        finally:
            session.close()

    def count(self, model_class: Type[Base], filters: Optional[Dict[str, Any]] = None) -> int:
        """
        レコード数をカウントする

        Args:
            model_class: カウント対象のモデルクラス
            filters: フィルタ条件の辞書

        Returns:
            レコード数
        """
        session = self.get_session()
        try:
            query = session.query(model_class)

            if filters:
                for key, value in filters.items():
                    if hasattr(model_class, key):
                        query = query.filter(getattr(model_class, key) == value)

            return query.count()

        except Exception as e:
            session.rollback()
            raise DatabaseError(MESSAGES["DATABASE_COUNT_ERROR"].format(error=str(e)))
        finally:
            session.close()

    @staticmethod
    def _model_to_dict(record) -> Dict[str, Any]:
        """モデルインスタンスを辞書に変換する"""
        if record is None:
            return {}
        return {c.name: getattr(record, c.name) for c in record.__table__.columns}
