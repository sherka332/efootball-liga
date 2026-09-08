from datetime import datetime
from pydantic import BaseModel, Field


class TelegramAuth(BaseModel):
    init_data: str


class TeamResponse(BaseModel):
    id: int
    name: str
    short_name: str
    logo_url: str | None = None
    participant_id: int | None = None

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    blocked: bool

    class Config:
        from_attributes = True


class MatchResponse(BaseModel):
    id: int
    round_number: int
    home_team_id: int
    away_team_id: int
    status: str
    deadline: datetime | None = None

    class Config:
        from_attributes = True

class ResultCreate(BaseModel):
    match_id: int
    home_goals: int = Field(ge=0, le=99)
    away_goals: int = Field(ge=0, le=99)


class ResultResponse(BaseModel):
    id: int
    match_id: int
    submitted_by: int
    home_goals: int
    away_goals: int
    confirmed_by: int | None = None
    submitted_at: datetime
    confirmed_at: datetime | None = None

    class Config:
        from_attributes = True

class StandingsRow(BaseModel):
    position: int
    team_id: int
    team_name: str
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int


class MessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    recipient_id: int | None = None

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    recipient_id: int | None
    text: str
    created_at: datetime
    deleted: bool

    class Config:
        from_attributes = True
