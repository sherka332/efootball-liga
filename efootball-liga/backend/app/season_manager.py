from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import settings
from .fixtures import generate_round_robin
from .models import Match, Result, Season, Team

TIMEZONE = ZoneInfo(settings.TIMEZONE)


def get_active_season(
    db: Session,
    league_id: int
):
    """
    Berilgan liga uchun faol mavsumni topadi.
    """

    return db.scalar(
        select(Season)
        .where(
            Season.league_id == league_id,
            Season.active.is_(True)
        )
        .order_by(Season.id.desc())
    )

def get_season_number(
    season_name: str
) -> int:
    """
    'Mavsum 1' -> 1
    'Mavsum 2' -> 2
    """

    try:
        return int(
            season_name.replace(
                "Mavsum ",
                ""
            ).strip()
        )
    except (ValueError, AttributeError):
        return 0

def get_next_season_number(
    db: Session,
    league_id: int
) -> int:
    """
    Shu liga uchun keyingi mavsum raqamini topadi.
    """

    seasons = db.scalars(
        select(Season)
        .where(
            Season.league_id == league_id
        )
    ).all()

numbers = [
        get_season_number(season.name)
        for season in seasons
    ]

    return max(numbers, default=0) + 1


def is_season_finished(
    db: Session,
    season_id: int
) -> bool:
    """
    Mavsum tugaganini tekshiradi.

    20 ta jamoa:
    38 tur:
    380 ta o'yin.

    Barcha 380 ta o'yin rasmiy
    tasdiqlangan natijaga ega bo'lsa,
    mavsum tugagan hisoblanadi.
    """

total_matches = db.scalar(
        select(func.count(Match.id))
        .where(
            Match.season_id == season_id
        )
    ) or 0

    if total_matches != 380:
        return False

    official_results = db.scalar(
        select(func.count(Result.id))
        .join(
            Match,
            Result.match_id == Match.id
        )
        .where(
            Match.season_id == season_id,
            Result.confirmed_by.is_not(None)
        )
    ) or 0

return official_results == 380


def create_next_season(
    db: Session,
    current_season: Season
):
    """
    Joriy mavsum tugagach avtomatik
    keyingi mavsumni yaratadi.

    Misol:
    Mavsum 1 -> Mavsum 2
    Mavsum 2 -> Mavsum 3
    """

    next_number = get_next_season_number(
        db,
        current_season.league_id
    )

next_name = f"Mavsum {next_number}"

    existing = db.scalar(
        select(Season)
        .where(
            Season.league_id == current_season.league_id,
            Season.name == next_name
        )
    )

    if existing:
        return existing

    next_season = Season(
        league_id=current_season.league_id,
        name=next_name,
        active=True,
        deadline_hour=current_season.deadline_hour,
        deadline_minute=current_season.deadline_minute
    )

urrent_season.active = False

    db.add(next_season)
    db.flush()

    current_teams = db.scalars(
        select(Team)
        .where(
            Team.season_id == current_season.id
        )
        .order_by(Team.id)
    ).all()

    if len(current_teams) != 20:
        raise ValueError(
            "Keyingi mavsumni yaratish uchun "
            "joriy mavsumda aynan 20 ta jamoa bo'lishi kerak."
        )

  for old_team in current_teams:

        new_team = Team(
            season_id=next_season.id,
            name=old_team.name,
            short_name=old_team.short_name,
            logo_url=old_team.logo_url,
            participant_id=None,
            blocked=False
        )

        db.add(new_team)

    db.flush()


now = datetime.now(TIMEZONE)

    next_day = now.date() + timedelta(days=1)

    first_match_date = datetime.combine(
        next_day,
        time(0, 0),
        tzinfo=TIMEZONE
    )

    generate_round_robin(
        db,
        next_season.id,
        first_match_date=first_match_date
    )

    return next_season

def check_and_start_next_season(
    db: Session,
    season_id: int
):
    """
    Mavsum tugagan bo'lsa,
    avtomatik keyingi mavsumni ishga tushiradi.

    Tugamagan bo'lsa None qaytaradi.
    """

    current_season = db.get(
        Season,
        season_id
    )

if not current_season:
        return None

    if not current_season.active:
        return None

    if not is_season_finished(
        db,
        current_season.id
    ):
        return None

    next_season = create_next_season(
        db,
        current_season
    )

    db.commit()

    return next_season
