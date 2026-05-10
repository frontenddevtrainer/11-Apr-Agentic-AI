"""
SQLite database layer using SQLAlchemy.
Defines tables for tickets, processing logs, and metrics.
"""

from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

from config.settings import SQLITE_DB_PATH

Base = declarative_base()


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # "app_review" or "support_email"
    category = Column(String, nullable=False)      # Bug, Feature Request, Praise, Complaint, Spam
    priority = Column(String, nullable=False)      # Critical, High, Medium, Low
    title = Column(String, nullable=False)
    description = Column(Text)
    technical_details = Column(Text)
    confidence_score = Column(Float)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ProcessingLog(Base):
    __tablename__ = "processing_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String, nullable=False)
    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    details = Column(Text)
    confidence = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, nullable=False)
    total_processed = Column(Integer)
    bugs_count = Column(Integer)
    features_count = Column(Integer)
    praise_count = Column(Integer)
    complaints_count = Column(Integer)
    spam_count = Column(Integer)
    avg_confidence = Column(Float)
    processing_time_seconds = Column(Float)
    accuracy = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def get_engine():
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{SQLITE_DB_PATH}", echo=False)


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    """Create all tables if they don't exist."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine
