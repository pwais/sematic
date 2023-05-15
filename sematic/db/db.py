"""
Module keeping the connection to the DB.
"""
# Standard Library
import typing
from contextlib import contextmanager

# Third-party
import sqlalchemy
import sqlalchemy.orm

# Sematic
from sematic.config.config import get_config


class DB:
    """
    Base class to describe SQLAlchemy database
    connections.
    """

    def __init__(self, url: str):
        self._engine = sqlalchemy.create_engine(
            url,
            # Recycle connections after 1 hour (3600s). This
            # helps prevent us from holding onto connections
            # when a DB server is trying to swap connections
            # gradually to a new instance.
            pool_recycle=3600,
            # Before getting a connection from the connection pool,
            # ping the DB to ensure that it's still a valid connection.
            # This prevents us from trying to use stale/bad connections
            # for real requests.
            pool_pre_ping=True,
        )
        self._Session = sqlalchemy.orm.sessionmaker(bind=self._engine)

    def get_engine(self) -> sqlalchemy.engine.Engine:
        return self._engine

    @contextmanager
    def get_session(self) -> typing.Generator[sqlalchemy.orm.Session, None, None]:
        session = self._Session()
        try:
            yield session
        finally:
            session.close()


_db_instance: typing.Optional[DB] = None


def db() -> DB:
    """
    Convenience method to access the current database
    connection.

    This should be the primary way any code accesses the DB.

    Example
    -------
    from sematic.db.db import db

    with db().get_session() as session:
        session.query(...)
    """
    global _db_instance
    if _db_instance is None:
        url = get_config().db_url
        _db_instance = DB(url)
    return _db_instance
