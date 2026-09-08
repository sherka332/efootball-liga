from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from .models import Team, Match


TIMEZONE = ZoneInfo("Asia/Tashkent")


def generate_round_robin(
    db: Session,
    season_id: int,
    first_match_date: datetime | None = None
):
    teams = db.query(Team).filter(
        Team.season_id == season_id
    ).order_by(
        Team.id
    ).all()

    if len(teams) != 20:
        raise ValueError(
            "Fixture yaratish uchun aynan 20 ta jamoa kerak."
        )

existing = db.query(Match).filter(
        Match.season_id == season_id
    ).count()

    if existing > 0:
        raise ValueError(
            "Bu mavsum uchun fixture allaqachon yaratilgan."
        )

    team_ids = [team.id for team in teams]

    rounds = []

    rotating = team_ids[:]

    # 19 tur
    for round_number in range(1, 20):

        matches = []

        for i in range(10):

            home = rotating[i]
            away = rotating[-(i + 1)]

            if round_number % 2 == 0:
                home, away = away, home

            matches.append(
                (home, away)
            )

rounds.append(matches)

        rotating = [
            rotating[0],
            rotating[-1],
            *rotating[1:-1]
        ]

    # Ikkinchi davra.
    # Birinchi davradagi uy/safar joylarini almashtiramiz.
    second_half = []

    for matches in rounds:

        reversed_matches = []

        for home, away in matches:
            reversed_matches.append(
                (away, home)
            )

second_half.append(
            reversed_matches
        )

    all_rounds = rounds + second_half

    if first_match_date is None:
        first_match_date = datetime.now(TIMEZONE)

    created = []

    for round_index, matches in enumerate(
        all_rounds,
        start=1
    ):

       round_date = first_match_date + timedelta(
            days=(round_index - 1) * 7
        )

        deadline = round_date.replace(
            hour=23,
            minute=30,
            second=0,
            microsecond=0
)

for home_team_id, away_team_id in matches:

            match = Match(
                season_id=season_id,
                round_number=round_index,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                status="scheduled",
                deadline=deadline
            )

            db.add(match)
            created.append(match)

    db.commit()

    return created
