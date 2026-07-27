# api/database.py
import os
import json
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cortexfas:cortexfas@db:5432/cortexfas")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    api_key = Column(String(64), unique=True, nullable=False)
    tier = Column(String(20), nullable=False, default="free")
    requests_used = Column(Integer, nullable=False, default=0)
    requests_limit = Column(Integer, nullable=False, default=10)
    activated_at = Column(DateTime, nullable=True)
    last_request_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))

class UsageLog(Base):
    __tablename__ = "usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    endpoint = Column(String(50), nullable=False)
    energy_score = Column(Float, nullable=True)
    lyapunov = Column(Float, nullable=True)
    regime = Column(String(30), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))

def get_db():
    return SessionLocal()

def upgrade_user_tier(email: str, tier: str, limit: int, db):
    db.query(User).filter(User.email == email).update({
        "tier": tier,
        "requests_limit": limit,
        "requests_used": 0
    })
    db.commit()

def downgrade_user_tier(email: str, tier: str, limit: int, db):
    db.query(User).filter(User.email == email).update({
        "tier": tier,
        "requests_limit": limit
    })
    db.commit()

def log_event(email: str, event_type: str, payload: dict, db):
    db.execute(text(
        "INSERT INTO events (user_email, event_type, payload) VALUES (:e, :t, :p)"
    ), {"e": email, "t": event_type, "p": json.dumps(payload)})
    db.commit()
