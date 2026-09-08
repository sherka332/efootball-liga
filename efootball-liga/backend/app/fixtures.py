from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Team, Match


TIMEZONE = ZoneInfo("Asia/Tashkent")


def generate_round_robin(
    db: Session,
    season_id: int,
    first_match_date: datetime | None = None
):
    """
    20 ta jamoa uchun 38 tur / 380 ta o'yin yaratadi.

    Har kuni 2 ta tur o'tkaziladi:

    1-kun  -> 1-2 tur
    2-kun  -> 3-4 tur
    3-kun  -> 5-6 tur
    ...
    19-kun -> 37-38 tur

    Har bir kunning deadline'i 23:30.
    """

teams = db.scalars(
        select(Team)
        .where(
            Team.season_id == season_id,
            Team.blocked == False
        )
        .order_by(Team.id)
    ).all()

    if len(teams) != 20:
        raise ValueError(
            "Fixture yaratish uchun aynan 20 ta faol jamoa kerak."
        )

existing = db.scalar(
        select(Match.id)
        .where(Match.season_id == season_id)
        .limit(1)
    )

    if existing is not None:
        raise ValueError(
            "Bu mavsum uchun fixture allaqachon yaratilgan."
        )

    team_ids = [team.id for team in teams]

# -----------------------------------
    # 1-19 turlar
    # -----------------------------------

    first_half = []

    rotating = team_ids[:]

    for round_number in range(1, 20):

        round_matches = []

        for i in range(10):

            home = rotating[i]
            away = rotating[-(i + 1)]

            if round_number % 2 == 0:
                home, away = away, home

            round_matches.append(
                (home, away)
            )

first_half.append(round_matches)

        # Circle method
        rotating = [
            rotating[0],
            rotating[-1],
            *rotating[1:-1]
        ]

    # -----------------------------------
    # 20-38 turlar
    # -----------------------------------

    second_half = []

    for round_matches in first_half:

        reversed_matches = []

        for home, away in round_matches:

            reversed_matches.append(
                (away, home)
            )

        second_half.append(
            reversed_matches
        )

all_rounds = first_half + second_half

    # -----------------------------------
    # Boshlanish kuni
    # -----------------------------------

    if first_match_date is None:
        first_match_date = datetime.now(TIMEZONE)

    # -----------------------------------
    # O'yinlarni yaratish
    # -----------------------------------

    created_matches = []

    for round_index, round_matches in enumerate(
        all_rounds,
        start=1
    ):

          # Har 2 ta tur bitta kunga tegishli.
        # 1-2 tur -> 1-kun
        # 3-4 tur -> 2-kun
        # 5-6 tur -> 3-kun
        day_number = (round_index - 1) // 2

        round_date = (
            first_match_date
            + timedelta(days=day_number)
        )

        # Shu kunning umumiy deadline'i
        deadline = round_date.replace(
            hour=23,
            minute=30,
            second=0,
            microsecond=0
        )

for home_team_id, away_team_id in round_matches:

            match = Match(
                season_id=season_id,
                round_number=round_index,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                status="scheduled",
                deadline=deadline
            )

            db.add(match)
            created_matches.append(match)

    db.commit()

    return created_matches
