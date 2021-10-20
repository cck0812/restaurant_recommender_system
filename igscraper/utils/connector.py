import logging

import sqlalchemy as sa
from sqlalchemy.orm import scoped_session, sessionmaker

from . import constants
from .singleton import Singleton

logger = logging.getLogger(__name__)


class ConnectFromPool(metaclass=Singleton):
    """Get connection from pool"""

    def __init__(self):
        self.engine = sa.create_engine(**constants.DB_PARAM)
        self.session = None
        logger.debug("Connected to database")

    def __enter__(self):
        self.session = scoped_session(sessionmaker(bind=self.engine))
        logger.debug("Established session of database")

        return self.session

    def __exit__(self, type, value, traceback):
        if value is not None:
            self.session.rollback()
            logger.error("Rollback all actions !")
        else:
            self.session.commit()
            self.session.remove()
            logger.debug("Closed the connection and commit")


def main():
    with ConnectFromPool() as session:
        pass


if __name__ == "__main__":
    format = "%(asctime)s %(thread)d %(name)s %(levelname)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG)
    main()
