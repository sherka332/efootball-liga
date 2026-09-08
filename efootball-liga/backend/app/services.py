from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import (
    Team,
    Match,
    Result,
    User,
)

TASHKENT = ZoneInfo(settings.TIMEZONE)


def get_current_time():
    return datetime.now(TASHKENT)


def is_deadline_passed(match: Match) -> bool:
    if not match.deadline:
        return False

    now = get_current_time()

    deadline = match.deadline

    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=TASHKENT)

    return now > deadline

def get_user_by_telegram_id(
    db: Session,
    telegram_id: int
):
    return db.scalar(
        select(User).where(
            User.telegram_id == telegram_id
        )
    )


def get_user_team(
    db: Session,
    user_id: int,
    season_id: int
):
    return db.scalar(
        select(Team).where(
            Team.participant_id == user_id,
            Team.season_id == season_id
        )
    )

def get_match_for_user(
    db: Session,
    match_id: int,
    user_id: int
):
    team = get_user_team(
        db,
        user_id,
        season_id=None
    )

    if not team:
        return None

    return db.scalar(
        select(Match).where(
            Match.id == match_id
        )
    )

def calculate_standings(
    db: Session,
    season_id: int
):
    teams = db.scalars(
        select(Team).where(
            Team.season_id == season_id
        )
    ).all()

    results = db.scalars(
        select(Result)
        .join(Match, Result.match_id == Match.id)
        .where(
            Match.season_id == season_id,
            Result.confirmed_by.is_not(None)
        )
    ).all()

table = {}

    for team in teams:
        table[team.id] = {
            "team_id": team.id,
            "team_name": team.name,
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_difference": 0,
            "points": 0,
}

for result in results:

        match = db.get(
            Match,
            result.match_id
        )

        if not match:
            continue

        home = table.get(match.home_team_id)
        away = table.get(match.away_team_id)

        if not home or not away:
            continue

        home["played"] += 1
        away["played"] += 1

        home["goals_for"] += result.home_goals
        home["goals_against"] += result.away_goals

        away["goals_for"] += result.away_goals
        away["goals_against"] += result.home_goals

        if result.home_goals > result.away_goals:

            home["wins"] += 1
            away["losses"] += 1

            home["points"] += 3

elif result.home_goals < result.away_goals:

            away["wins"] += 1
            home["losses"] += 1

            away["points"] += 3

        else:

            home["draws"] += 1
            away["draws"] += 1

            home["points"] += 1
            away["points"] += 1

    for row in table.values():
        row["goal_difference"] = (
            row["goals_for"]
            - row["goals_against"]
        )

standings = list(table.values())

    standings.sort(
        key=lambda x: (
            -x["points"],
            -x["goal_difference"],
            -x["goals_for"],
            x["team_name"].lower()
        )
    )

    for index, row in enumerate(
        standings,
        start=1
    ):
        row["position"] = index

    return standings
