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
    20 ta jamoa uchun:

    38 ta tur
    Har turda 10 ta o'yin
    Jami 380 ta o'yin

    Har bir jamoa boshqalar bilan
    uyda va safarda bir martadan o'ynaydi.
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

    # Shu mavsumda fixture oldin yaratilganmi?
    existing_count = db.scalar(
        select(Match.id)
        .where(
            Match.season_id == season_id
        )
        .limit(1)
    )

if existing_count is not None:
        raise ValueError(
            "Bu mavsum uchun fixture allaqachon yaratilgan."
        )

    team_ids = [team.id for team in teams]

    # Birinchi 19 tur
    first_half = []

    rotating = team_ids[:]

    for round_number in range(1, 20):

        round_matches = []

        for i in range(10):

            home = rotating[i]
            away = rotating[-(i + 1)]

            # Uy/safar balansini o'zgartirib boramiz
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

# Ikkinchi 19 tur:
    # birinchi yarimdagi barcha o'yinlarning
    # home/away joyi almashtiriladi.
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

# Boshlanish sanasi berilmasa,
    # hozirgi vaqt olinadi.
    if first_match_date is None:
        first_match_date = datetime.now(TIMEZONE)

    created_matches = []

    for round_number, round_matches in enumerate(
        all_rounds,
        start=1
    ):

        # Har tur 7 kun oralig'ida
        round_date = (
            first_match_date
            + timedelta(
                days=(round_number - 1) * 7
            )
        )

# Har tur deadline'i 23:30
        deadline = round_date.replace(
            hour=23,
            minute=30,
            second=0,
            microsecond=0
        )

        for home_team_id, away_team_id in round_matches:

            match = Match(
                season_id=season_id,
                round_number=round_number,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                status="scheduled",
                deadline=deadline
            )

db.add(match)
            created_matches.append(match)

    db.commit()

    return created_matches
