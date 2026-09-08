from sqlalchemy import select

from .database import SessionLocal, Base, engine
from .models import League, Season, Team


LA_LIGA_TEAMS = [
    ("Athletic Club", "ATH"),
    ("Atlético de Madrid", "ATM"),
    ("CA Osasuna", "OSA"),
    ("Celta", "CEL"),
    ("Deportivo Alavés", "ALA"),
    ("Elche CF", "ELC"),
    ("FC Barcelona", "BAR"),
    ("Getafe CF", "GET"),
    ("Levante UD", "LEV"),
    ("Málaga CF", "MAL"),
    ("R. Racing Club", "RAC"),
    ("Rayo Vallecano", "RAY"),
    ("RC Deportivo", "DEP"),
    ("RCD Espanyol de Barcelona", "ESP"),
    ("Real Betis", "BET"),
    ("Real Madrid", "RMA"),
    ("Real Sociedad", "RSO"),
    ("Sevilla FC", "SEV"),
    ("Valencia CF", "VAL"),
    ("Villarreal CF", "VIL"),
]

PREMIER_LEAGUE_TEAMS = [
    ("AFC Bournemouth", "BOU"),
    ("Arsenal", "ARS"),
    ("Aston Villa", "AVL"),
    ("Brentford", "BRE"),
    ("Brighton & Hove Albion", "BHA"),
    ("Chelsea", "CHE"),
    ("Coventry City", "COV"),
    ("Crystal Palace", "CRY"),
    ("Everton", "EVE"),
    ("Fulham", "FUL"),
    ("Hull City", "HUL"),
    ("Ipswich Town", "IPS"),
    ("Leeds United", "LEE"),
    ("Liverpool", "LIV"),
    ("Manchester City", "MCI"),
    ("Manchester United", "MUN"),
    ("Newcastle United", "NEW"),
    ("Nottingham Forest", "NFO"),
    ("Sunderland", "SUN"),
    ("Tottenham Hotspur", "TOT"),
]

def create_league(
    db,
    league_name,
    country,
    teams
):
    # Liga mavjud bo'lmasa yaratamiz
    league = db.scalar(
        select(League).where(
            League.name == league_name
        )
    )

    if not league:
        league = League(
            name=league_name,
            country=country,
            active=True
        )

        db.add(league)
        db.flush()

        print(f"✅ Liga yaratildi: {league_name}")

# Birinchi mavsum
    # Mavsum nomida yil ishlatilmaydi.
    season = db.scalar(
        select(Season).where(
            Season.league_id == league.id,
            Season.name == "Mavsum 1"
        )
    )

 if not season:
        season = Season(
            league_id=league.id,
            name="Mavsum 1",
            active=True,
            deadline_hour=23,
            deadline_minute=30
        )

        db.add(season)
        db.flush()

print(
            f"✅ Mavsum 1 yaratildi: {league_name}"
        )

    # Jamoalarni qo'shamiz
    existing_teams = db.scalars(
        select(Team).where(
            Team.season_id == season.id
        )
    ).all()

existing_names = {
        team.name
        for team in existing_teams
    }

    for name, short_name in teams:

        if name in existing_names:
            continue

        team = Team(
            season_id=season.id,
            name=name,
            short_name=short_name,
            logo_url=None,
            participant_id=None,
            blocked=False
        )

db.add(team)

    db.commit()

    print(
        f"✅ {league_name}: "
        f"{len(teams)} ta jamoa tayyor."
    )


def main():
    print("🚀 Database seed boshlandi...")

    # Jadvallar mavjud bo'lmasa yaratadi
    Base.metadata.create_all(
        bind=engine
    )

    db = SessionLocal()

try:

        create_league(
            db,
            "La Liga",
            "Ispaniya",
            LA_LIGA_TEAMS
        )

        create_league(
            db,
            "Premier League",
            "Angliya",
            PREMIER_LEAGUE_TEAMS
        )

print("")
        print("🎉 Seed muvaffaqiyatli tugadi!")
        print("")
        print("🇪🇸 La Liga")
        print("   └── Mavsum 1")
        print("       └── 20 ta jamoa")
        print("")
        print("🏴 Premier League")
        print("   └── Mavsum 1")
        print("       └── 20 ta jamoa")
        print("")
        print("⏰ Natija deadline: 23:30")

    finally:
        db.close()


if name == "main":
    main()
