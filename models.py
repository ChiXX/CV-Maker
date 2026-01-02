from sqlalchemy import create_engine, Column, Integer, String, Text, LargeBinary, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Application(Base):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    jb_url = Column(String, nullable=False)
    jd_text = Column(Text, nullable=False)
    company = Column(String, nullable=False)
    title = Column(String, nullable=False)
    cv_pdf = Column(LargeBinary, nullable=True)
    cl_pdf = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Application(id={self.id}, company='{self.company}', title='{self.title}')>"
