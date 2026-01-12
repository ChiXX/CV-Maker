import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum as SQLEnum,
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ApplicationStatus(str, enum.Enum):
    archive = "archive"
    submitted = "submitted"
    interviewing = "interviewing"
    offered = "offered"
    failed = "failed"


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_url = Column(String, nullable=False, unique=True, index=True)
    jd_text = Column(Text, nullable=False)
    company = Column(String, nullable=False)
    title = Column(String, nullable=False)
    cv_latex = Column(Text, nullable=True)
    cl_latex = Column(Text, nullable=True)
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.submitted, nullable=False)
    comment = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Application(id={self.id}, company='{self.company}', title='{self.title}')>"
