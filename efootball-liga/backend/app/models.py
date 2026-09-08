from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Text
)

from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class League(Base):
    tablename = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)

name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

class Season(Base):
    tablename = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True)

    league_id: Mapped[int] = mapped_column(
        ForeignKey("leagues.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

deadline_hour: Mapped[int] = mapped_column(
        Integer,
        default=23
    )

    deadline_minute: Mapped[int] = mapped_column(
        Integer,
        default=30
    )


class User(Base):
    tablename = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    telegram_id: Mapped[int] = mapped_column(
        unique=True,
        index=True,
        nullable=False
    )

username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    first_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

class Team(Base):
    tablename = "teams"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    short_name: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

logo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    participant_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )


table_args = (
        UniqueConstraint(
            "season_id",
            "name",
            name="uq_team_season_name"
        ),
    )


class Match(Base):
    tablename = "matches"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id"),
        nullable=False
    )
round_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    home_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        nullable=False
    )

    away_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        nullable=False
    )

status: Mapped[str] = mapped_column(
        String(40),
        default="scheduled"
    )

    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )


class Result(Base):
    tablename = "results"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id"),
        unique=True,
        nullable=False
    )

    submitted_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    home_goals: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )


away_goals: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    confirmed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

submitted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

class Message(Base):
    tablename = "messages"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

recipient_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )
