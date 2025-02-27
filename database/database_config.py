# DATABASE CONFIG

# ---------------------------------------------------------------------------------------------------------------------
# IMPORT LIBRARIES
from typing import Optional
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


# ---------------------------------------------------------------------------------------------------------------------
# CONFIGURATION CLASS

class DatabaseConfig:
    """
    Database configuration
    """

    def __init__(self, database_info: dict, database_name: str = 'default') -> None:
        self.name: str = database_name

        self._host: str = database_info[database_name]['host']
        self._db_name: str = database_info[database_name]['database']
        self._user: str = database_info[database_name]['user']
        self._password: str = database_info[database_name]['password']
        self._port: int = database_info[database_name]['port']

        self._session: Optional[scoped_session] = None

    def get_engine_url(self) -> str:
        database_url: str = f"postgresql+psycopg2://{self._user}:{quote_plus(self._password)}@" \
                            f"{self._host}:{self._port}/{self._db_name}"
        return database_url

    def get_session(self) -> scoped_session:
        if self._session is None:
            engine = create_engine(self.get_engine_url(), pool_pre_ping=True)
            self._session = scoped_session(sessionmaker(bind=engine))
        return self._session
