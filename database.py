from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_URL = "sqlite:///loja.db"

Base = declarative_base()

class Database:
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia.engine = create_engine(
                DB_URL, connect_args={"check_same_thread": False}
            )
            cls._instancia.SessionLocal = sessionmaker(
                bind=cls._instancia.engine, autoflush=False, autocommit=False
            )
        return cls._instancia


def init_db():
    import models
    Base.metadata.create_all(bind=Database().engine)


def get_db():
    db = Database().SessionLocal()
    try:
        yield db
    finally:
        db.close()