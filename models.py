from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    jb_url = Column(String, nullable=False, unique=True, index=True)
    jd_text = Column(Text, nullable=False)
    company = Column(String, nullable=False)
    title = Column(String, nullable=False)
    cv_latex = Column(Text, nullable=True)
    cl_latex = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Application(id={self.id}, company='{self.company}', title='{self.title}')>"
