from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from .models import (
    User,
    Team,
    Match,
    Result,
    Message,
    Season,
)

from .schemas import (
    TelegramAuth,
    ResultCreate,
    MessageCreate,
)
from .services import (
    calculate_standings,
    get_current_time,
    is_deadline_passed,
)


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="eFootball Liga API",
    version="1.0.0"
)


# =========================================================
# BASIC
# =========================================================

@app.get("/")
def root():
    return {
        "success": True,
        "message": "eFootball Liga API ishlayapti"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# =========================================================
# HELPERS
# =========================================================

def get_user(
    db: Session,
    telegram_id: int
):
    user = db.scalar(
        select(User).where(
            User.telegram_id == telegram_id
        )
    )

if not user:
        raise HTTPException(
            status_code=404,
            detail="Foydalanuvchi topilmadi"
        )

    if user.blocked:
        raise HTTPException(
            status_code=403,
            detail="Siz bloklangansiz"
        )

return user


def get_active_season(
    db: Session,
    league_name: str | None = None
):
    query = select(Season).where(
        Season.active == True
    )


seasons = db.scalars(query).all()

    if not seasons:
        raise HTTPException(
            status_code=404,
            detail="Faol mavsum topilmadi"
        )


if league_name:
        from .models import League

        season = db.scalar(
            select(Season)
            .join(
                League,
                Season.league_id == League.id
            )
            .where(
                Season.active == True,
                League.name == league_name
            )
        )

if not season:
            raise HTTPException(
                status_code=404,
                detail="Ushbu liga uchun faol mavsum topilmadi"
            )

        return season

    return seasons[0]

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

# =========================================================
# TELEGRAM AUTH
# =========================================================

@app.post("/api/auth/telegram")
def telegram_auth(
    data: TelegramAuth,
    db: Session = Depends(get_db)
):
  """
    Hozircha development uchun.
    
    Production versiyada Telegram WebApp initData
    server tomonida HMAC orqali tekshiriladi.
    """

    try:
        import json
        from urllib.parse import parse_qs

        parsed = parse_qs(
            data.init_data
        )

user_raw = parsed.get(
            "user",
            [None]
        )[0]

        if not user_raw:
            raise HTTPException(
                status_code=400,
                detail="Telegram user ma'lumoti topilmadi"
            )

        telegram_user = json.loads(
            user_raw
        )

telegram_id = int(
            telegram_user["id"]
        )

        username = telegram_user.get(
            "username"
        )

        first_name = telegram_user.get(
            "first_name"
        )

except Exception:
        raise HTTPException(
            status_code=400,
            detail="Telegram ma'lumotlari noto'g'ri"
        )

    user = db.scalar(
        select(User).where(
            User.telegram_id == telegram_id
        )
    )

if not user:

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name
        )

        db.add(user)
        db.commit()
        db.refresh(user)

else:

        user.username = username
        user.first_name = first_name

        db.commit()
        db.refresh(user)

return {
        "success": True,
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name
        }
}


# =========================================================
# LEAGUES
# =========================================================

@app.get("/api/leagues")
def get_leagues(
    db: Session = Depends(get_db)
):
    from .models import League

    leagues = db.scalars(
        select(League)
    ).all()

return [
        {
            "id": league.id,
            "name": league.name,
            "country": league.country,
            "active": league.active
        }
        for league in leagues
]


# =========================================================
# TEAMS
# =========================================================

@app.get("/api/teams")
def get_teams(
    league: str | None = None,
    db: Session = Depends(get_db)
):

  from .models import League

    query = (
        select(Team)
        .join(
            Season,
            Team.season_id == Season.id
        )
        .join(
            League,
            Season.league_id == League.id
        )
        .where(
            Season.active == True
        )
    )

if league:
        query = query.where(
            League.name == league
        )

    teams = db.scalars(
        query
    ).all()


return [
        {
            "id": team.id,
            "name": team.name,
            "short_name": team.short_name,
            "logo_url": team.logo_url,
            "participant_id": team.participant_id,
            "available": (
                team.participant_id is None
                and not team.blocked
            )
        }
        for team in teams
]


# =========================================================
# SELECT TEAM
# =========================================================

@app.post("/api/teams/{team_id}/select")
def select_team(
    team_id: int,
    telegram_id: int,
    db: Session = Depends(get_db)
):

  user = get_user(
        db,
        telegram_id
    )

    team = db.get(
        Team,
        team_id
    )

    if not team:
        raise HTTPException(
            status_code=404,
            detail="Jamoa topilmadi"
        )

if team.blocked:
        raise HTTPException(
            status_code=400,
            detail="Bu jamoa bloklangan"
        )

    if team.participant_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Bu jamoani boshqa ishtirokchi tanlagan"
        )

existing_team = get_user_team(
        db,
        user.id,
        team.season_id
    )

    if existing_team:
        raise HTTPException(
            status_code=400,
            detail=(
                "Siz allaqachon jamoa tanlagansiz: "
                + existing_team.name
            )
        )

team.participant_id = user.id

    db.commit()
    db.refresh(team)

    return {
        "success": True,
        "message": f"{team.name} sizga biriktirildi",
        "team": {
            "id": team.id,
            "name": team.name,
            "logo_url": team.logo_url
        }
    }


# =========================================================
# MY TEAM
# =========================================================

@app.get("/api/my-team")
def my_team(
    telegram_id: int,
    season_id: int,
    db: Session = Depends(get_db)
):

  user = get_user(
        db,
        telegram_id
    )

    team = get_user_team(
        db,
        user.id,
        season_id
    )

    if not team:
        return {
            "success": True,
            "team": None
        }

return {
        "success": True,
        "team": {
            "id": team.id,
            "name": team.name,
            "short_name": team.short_name,
            "logo_url": team.logo_url
        }
}


# =========================================================
# MY MATCHES
# =========================================================

@app.get("/api/my-matches")
def my_matches(
    telegram_id: int,
    season_id: int,
    round_number: int | None = None,
    db: Session = Depends(get_db)
):

  user = get_user(
        db,
        telegram_id
    )

    team = get_user_team(
        db,
        user.id,
        season_id
    )

if not team:
        raise HTTPException(
            status_code=404,
            detail="Sizga jamoa biriktirilmagan"
        )

    query = select(Match).where(
        Match.season_id == season_id
    )

    query = query.where(
        (
            Match.home_team_id == team.id
        )
        |
        (
            Match.away_team_id == team.id
        )
    )

if round_number:
        query = query.where(
            Match.round_number == round_number
        )

    query = query.order_by(
        Match.round_number,
        Match.id
    )

    matches = db.scalars(
        query
    ).all()

response = []

    for match in matches:

        home = db.get(
            Team,
            match.home_team_id
        )

        away = db.get(
            Team,
            match.away_team_id
        )

result = db.scalar(
            select(Result).where(
                Result.match_id == match.id
            )
)

response.append(
            {
                "id": match.id,
                "round_number": match.round_number,
                "home": {
                    "id": home.id,
                    "name": home.name,
                    "logo_url": home.logo_url
                },
                "away": {
                    "id": away.id,
                    "name": away.name,
                    "logo_url": away.logo_url
                },
              "status": match.status,
                "deadline": match.deadline,
                "result": (
                    {
                        "home_goals": result.home_goals,
                        "away_goals": result.away_goals,
                        "confirmed": (
                            result.confirmed_by
                            is not None
                        )
                    }
                    if result
                    else None
                )
            }
        )

    return response


# =========================================================
# SUBMIT RESULT
# =========================================================

@app.post("/api/results")
def submit_result(
    telegram_id: int,
    data: ResultCreate,
    db: Session = Depends(get_db)
):

  user = get_user(
        db,
        telegram_id
    )

    match = db.get(
        Match,
        data.match_id
    )

if not match:
        raise HTTPException(
            status_code=404,
            detail="Match topilmadi"
        )

    if is_deadline_passed(match):
        raise HTTPException(
            status_code=400,
            detail="Natija topshirish vaqti tugagan"
        )

home_team = db.get(
        Team,
        match.home_team_id
    )

    away_team = db.get(
        Team,
        match.away_team_id
    )

if (
        home_team.participant_id != user.id
        and
        away_team.participant_id != user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Bu match sizniki emas"
        )

existing = db.scalar(
        select(Result).where(
            Result.match_id == match.id
        )
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Bu match uchun natija allaqachon yuborilgan"
        )

result = Result(
        match_id=match.id,
        submitted_by=user.id,
        home_goals=data.home_goals,
        away_goals=data.away_goals
)

db.add(result)

    match.status = "pending_confirmation"

    db.commit()
    db.refresh(result)

    opponent_id = (
        away_team.participant_id
        if home_team.participant_id == user.id
        else home_team.participant_id
    )


return {
        "success": True,
        "message": "Natija yuborildi. Raqib tasdiqlashi kerak.",
        "result_id": result.id,
        "opponent_user_id": opponent_id
          }


# =========================================================
# CONFIRM RESULT
# =========================================================

@app.post("/api/results/{result_id}/confirm")
def confirm_result(
    result_id: int,
    telegram_id: int,
    db: Session = Depends(get_db)
):

  user = get_user(
        db,
        telegram_id
    )

    result = db.get(
        Result,
        result_id
    )

if not result:
        raise HTTPException(
            status_code=404,
            detail="Natija topilmadi"
        )

    if result.confirmed_by:
        raise HTTPException(
            status_code=400,
            detail="Natija allaqachon tasdiqlangan"
        )


match = db.get(
        Match,
        result.match_id
    )

    home_team = db.get(
        Team,
        match.home_team_id
    )

    away_team = db.get(
        Team,
        match.away_team_id
    )

if (
        home_team.participant_id != user.id
        and
        away_team.participant_id != user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Siz bu natijani tasdiqlay olmaysiz"
        )

if result.submitted_by == user.id:
        raise HTTPException(
            status_code=400,
            detail="O'zingiz yuborgan natijani tasdiqlay olmaysiz"
        )

    result.confirmed_by = user.id
    result.confirmed_at = datetime.utcnow()

    match.status = "official"

db.commit()

    return {
        "success": True,
        "message": "Natija tasdiqlandi. Turnir jadvali yangilandi."
    }


# =========================================================
# REJECT RESULT
# =========================================================

@app.post("/api/results/{result_id}/reject")
def reject_result(
    result_id: int,
    telegram_id: int,
    db: Session = Depends(get_db)
):

  user = get_user(
        db,
        telegram_id
    )

    result = db.get(
        Result,
        result_id
    )


if not result:
        raise HTTPException(
            status_code=404,
            detail="Natija topilmadi"
        )

    match = db.get(
        Match,
        result.match_id
    )

home_team = db.get(
        Team,
        match.home_team_id
    )

    away_team = db.get(
        Team,
        match.away_team_id
    )

if (
        home_team.participant_id != user.id
        and
        away_team.participant_id != user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Siz bu natijani rad eta olmaysiz"
        )

if result.submitted_by == user.id:
        raise HTTPException(
            status_code=400,
            detail="O'zingiz yuborgan natijani rad eta olmaysiz"
        )

    match.status = "disputed"

    db.commit()

return {
        "success": True,
        "message": (
            "Natija rad etildi. "
            "Admin ko'rib chiqishi kerak."
        )
}


# =========================================================
# STANDINGS
# =========================================================

@app.get("/api/standings")
def standings(
    season_id: int,
    db: Session = Depends(get_db)
):
    table = calculate_standings(
        db,
        season_id
    )

return {
        "success": True,
        "standings": table
}



# =========================================================
# ROUND FIXTURES
# =========================================================

@app.get("/api/round/{round_number}")
def round_matches(
    round_number: int,
    season_id: int,
    db: Session = Depends(get_db)
):

  matches = db.scalars(
        select(Match).where(
            Match.season_id == season_id,
            Match.round_number == round_number
        ).order_by(
            Match.id
        )
    ).all()

    response = []


for match in matches:

        home = db.get(
            Team,
            match.home_team_id
        )

        away = db.get(
            Team,
            match.away_team_id
        )

result = db.scalar(
            select(Result).where(
                Result.match_id == match.id
            )
)

response.append(
            {
                "id": match.id,
                "round": match.round_number,
                "home": {
                    "id": home.id,
                    "name": home.name,
                    "logo_url": home.logo_url
                },
                "away": {
                    "id": away.id,
                    "name": away.name,
                    "logo_url": away.logo_url
                },
              "status": match.status,
                "deadline": match.deadline,
                "result": (
                    {
                        "home_goals": result.home_goals,
                        "away_goals": result.away_goals,
                        "official": (
                            result.confirmed_by
                            is not None
                        )
                    }
                    if result
                    else None
                )
            }
)

return {
        "success": True,
        "round": round_number,
        "matches": response
}


# =========================================================
# CHAT
# =========================================================

@app.get("/api/messages")
def get_messages(
    telegram_id: int,
    recipient_id: int | None = None,
    db: Session = Depends(get_db)
):

  user = get_user(
        db,
        telegram_id
    )

    query = select(Message).where(
        Message.deleted == False
    )

if recipient_id is None:

        query = query.where(
            Message.recipient_id.is_(None)
        )

else:

        query = query.where(
            (
                (
                    Message.sender_id == user.id
                )
                &
                (
                    Message.recipient_id
                    == recipient_id
                )
            )
            |
            (
                (
                    Message.sender_id
                    == recipient_id
                )
                &
                (
                    Message.recipient_id
                    == user.id
                )
            )
        )

messages = db.scalars(
        query.order_by(
            Message.created_at
        )
    ).all()


return [
        {
            "id": message.id,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "text": message.text,
            "created_at": message.created_at,
            "deleted": message.deleted
        }
        for message in messages
]

@app.post("/api/messages")
def send_message(
    telegram_id: int,
    data: MessageCreate,
    db: Session = Depends(get_db)
):
    user = get_user(
        db,
        telegram_id
    )

message = Message(
        sender_id=user.id,
        recipient_id=data.recipient_id,
        text=data.text
    )

    db.add(message)
    db.commit()
    db.refresh(message)

return {
        "success": True,
        "message": {
            "id": message.id,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "text": message.text,
            "created_at": message.created_at
        }
}


# =========================================================
# ADMIN CHECK
# =========================================================

def check_admin(
    telegram_id: int
):
    if telegram_id not in settings.admin_ids:
        raise HTTPException(
            status_code=403,
            detail="Admin huquqi kerak"
        )



# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.get("/api/admin/dashboard")
def admin_dashboard(
    telegram_id: int,
    db: Session = Depends(get_db)
):

  check_admin(telegram_id)

    users_count = db.query(User).count()
    teams_count = db.query(Team).count()
    matches_count = db.query(Match).count()

    pending_results = db.query(Result).join(
        Match,
        Result.match_id == Match.id
    ).filter(
        Match.status.in_([
            "pending_confirmation",
            "disputed"
        ])
    ).count()

return {
        "users": users_count,
        "teams": teams_count,
        "matches": matches_count,
        "pending_results": pending_results
}


# =========================================================
# ADMIN EDIT RESULT
# =========================================================

@app.post("/api/admin/results/{match_id}")
def admin_set_result(
    match_id: int,
    telegram_id: int,
    home_goals: int,
    away_goals: int,
    db: Session = Depends(get_db)
):

  check_admin(telegram_id)

    match = db.get(
        Match,
        match_id
    )

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match topilmadi"
        )


result = db.scalar(
        select(Result).where(
            Result.match_id == match_id
        )
        )

if not result:

        result = Result(
            match_id=match_id,
            submitted_by=(
                db.scalar(
                    select(User).where(
                        User.telegram_id
                        == telegram_id
                    )
                ).id
            ),
          home_goals=home_goals,
            away_goals=away_goals,
            confirmed_by=(
                db.scalar(
                    select(User).where(
                        User.telegram_id
                        == telegram_id
                    )
                ).id
            ),
            confirmed_at=datetime.utcnow()
        )

       db.add(result)

else:

        result.home_goals = home_goals
        result.away_goals = away_goals

        result.confirmed_by = (
            db.scalar(
                select(User).where(
                    User.telegram_id
                    == telegram_id
                )
            ).id
        )

        result.confirmed_at = datetime.utcnow()

match.status = "official"

    db.commit()

    return {
        "success": True,
        "message": "Admin natijani saqladi"
    }
