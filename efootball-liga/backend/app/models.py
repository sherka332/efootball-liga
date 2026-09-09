from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    telegram_id = Column(String(64), unique=True, nullable=True, index=True)
    first_name = Column(String(120), nullable=True)
    last_name = Column(String(120), nullable=True)
    telegram_username = Column(String(120), nullable=True)
    role = Column(String(20), default="PLAYER", nullable=False)
    is_banned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Season(Base):
    __tablename__ = "seasons"
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    status = Column(String(30), default="OPEN", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class SeasonPlayer(Base):
    __tablename__ = "season_players"
    id = Column(Integer, primary_key=True)
    season_id = Column(Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    __table_args__ = (UniqueConstraint("season_id", "user_id", name="uq_season_player"),)

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    season_id = Column(Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    round_number = Column(Integer, nullable=False)
    home_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    away_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    played = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
