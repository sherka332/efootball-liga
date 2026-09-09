from typing import Optional
from pydantic import BaseModel, Field

class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=4, max_length=200)

class LoginIn(BaseModel):
    username: str
    password: str

class TelegramAuthIn(BaseModel):
    init_data: str = Field(min_length=1)

class SeasonCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)

class StatusIn(BaseModel):
    status: str

class ScoreIn(BaseModel):
    home_score: int = Field(ge=0, le=99)
    away_score: int = Field(ge=0, le=99)

class UserOut(BaseModel):
    id: int
    username: str
    telegram_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    telegram_username: Optional[str] = None
    role: str
    is_banned: bool

    class Config:
        from_attributes = True
