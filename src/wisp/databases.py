from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
engine = create_engine("sqlite:///messages.db")

class Base(DeclarativeBase):
    pass

