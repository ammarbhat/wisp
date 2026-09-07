from sqlalchemy.orm import Mapped, mapped_column
from wisp.databases import Base

class Note(Base):
    __tablename__ = "messages"
    id : Mapped[int] = mapped_column(primary_key=True)
    message : Mapped[str]