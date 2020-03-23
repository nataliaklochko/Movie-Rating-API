from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///movies-rating.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()


@contextmanager
def create_session(**kwargs):
    new_session = Session(**kwargs)
    try:
        yield new_session
        new_session.commit()
    except Exception:
        new_session.rollback()
        raise
    finally:
        new_session.close()


def init_db():
    Base.metadata.create_all(bind=engine)
