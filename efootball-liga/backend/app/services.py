from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import Team, Match, Result, User


TIMEZONE = ZoneInfo(settings.TIMEZONE)


def get_current_time() -> datetime:
    """
    Toshkent vaqtini qaytaradi.
    """
    return datetime.now(TIMEZONE)

def get_user_by_telegram_id(
    db: Session,
    telegram_id: int
):
    """
    Telegram ID orqali foydalanuvchini topadi.
    """
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
    """
    Foydalanuvchining shu mavsumdagi
    jamoasini topadi.
    """
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
"""
    Foydalanuvchi ushbu o'yinda
    qatnashayotganini tekshiradi.
    """

    match = db.get(Match, match_id)

    if not match:
        return None

    team = get_user_team(
        db,
        user_id,
        match_season_id(match)
    )

if not team:
        return None

    if team.id not in (
        match.home_team_id,
        match.away_team_id
    ):
        return None

    return match


def match_season_id(match: Match) -> int:
    """
    Match season ID sini qaytaradi.
    """
    return match.season_id

def get_match_opponent_team_id(
    db: Session,
    match: Match,
    user_id: int
):
    """
    Foydalanuvchining raqibi jamoasi ID sini topadi.
    """

    user_team = get_user_team(
        db,
        user_id,
        match.season_id
    )

    if not user_team:
        return None

if match.home_team_id == user_team.id:
        return match.away_team_id

    if match.away_team_id == user_team.id:
        return match.home_team_id

    return None


def get_match_participant_ids(
    db: Session,
    match: Match
):
    """
    Matchdagi ikkala ishtirokchining
    User ID larini qaytaradi.
    """

    home_team = db.get(
        Team,
        match.home_team_id
    )

away_team = db.get(
        Team,
        match.away_team_id
    )

    if not home_team or not away_team:
        return None, None

    return (
        home_team.participant_id,
        away_team.participant_id
    )


def is_deadline_passed(
    match: Match
) -> bool:
    """
    O'yin deadline'i o'tgan yoki yo'qligini tekshiradi.
    """

    if not match.deadline:
        return False

now = get_current_time()

    deadline = match.deadline

    if deadline.tzinfo is None:
        deadline = deadline.replace(
            tzinfo=TIMEZONE
        )

    return now > deadline


def get_seconds_until_deadline(
    match: Match
) -> int:
    """
    Deadlinegacha qolgan soniyalarni qaytaradi.
    """

    if not match.deadline:
        return 0

now = get_current_time()

    deadline = match.deadline

    if deadline.tzinfo is None:
        deadline = deadline.replace(
            tzinfo=TIMEZONE
        )

    seconds = int(
        (deadline - now).total_seconds()
    )

    return max(seconds, 0)


def can_submit_result(
    db: Session,
    match: Match,
    user_id: int
) -> tuple[bool, str]:
    """
    Foydalanuvchi natija yubora oladimi?
    """

    if not get_match_for_user(
        db,
        match.id,
        user_id
    ):
        return (
            False,
            "Bu o'yinda siz qatnashmaysiz."
        )

    if match.status in (
        "completed",
        "confirmed"
    ):
        return (
            False,
            "Bu o'yin natijasi allaqachon tasdiqlangan."
        )

    if match.status == "disputed":
        return (
            False,
            "Bu natija admin ko‘rib chiqishida."
        )

    if is_deadline_passed(match):
        return (
            False,
            "⏰ Natija topshirish vaqti 23:30 da tugagan."
        )

existing_result = db.scalar(
        select(Result).where(
            Result.match_id == match.id
        )
    )

    if existing_result:
        return (
            False,
            "Bu o'yin uchun natija allaqachon yuborilgan."
        )

    return True, ""

def calculate_standings(
    db: Session,
    season_id: int
):
    """
    Tasdiqlangan natijalar asosida
    liga jadvalini hisoblaydi.

    G'alaba = 3 ochko
    Durang = 1 ochko
    Mag'lubiyat = 0 ochko
    """

    teams = db.scalars(
        select(Team)
        .where(
            Team.season_id == season_id
        )
    ).all()

results = db.scalars(
        select(Result)
        .join(
            Match,
            Result.match_id == Match.id
        )
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

        home = table.get(
            match.home_team_id
        )

        away = table.get(
            match.away_team_id
        )

        if not home or not away:
            continue

        home["played"] += 1
        away["played"] += 1

        home["goals_for"] += (
            result.home_goals
        )

        home["goals_against"] += (
            result.away_goals
        )

away["goals_for"] += (
            result.away_goals
        )

        away["goals_against"] += (
            result.home_goals
        )

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

    standings = list(
        table.values()
    )

standings.sort(
        key=lambda x: (
            -x["points"],
            -x["goal_difference"],
            -x["goals_for"],
            x["team_name"].lower()
        )
    )

    for position, row in enumerate(
        standings,
        start=1
    ):
        row["position"] = position

    return standings
    
