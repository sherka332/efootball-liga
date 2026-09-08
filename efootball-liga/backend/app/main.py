from datetime import datetime
from hashlib import sha256
from hmac import compare_digest
from urllib.parse import parse_qsl
import hmac
import json

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from .models import (
    League,
    Season,
    User,
    Team,
    Match,
    Result,
    Message,
)
from .schemas import ResultCreate, MessageCreate
from .services import (
    calculate_standings,
    get_user_by_telegram_id,
    get_user_team,
    can_submit_result,
    get_match_participant_ids,
)
from .season_manager import check_and_start_next_season


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="eFootball Liga API",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "name": "eFootball Liga API",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


def validate_telegram_init_data(init_data: str):
    if not init_data:
        raise HTTPException(
            status_code=401,
            detail="Telegram autentifikatsiya ma'lumotlari mavjud emas."
        )

    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Telegram initData noto'g'ri."
        )

    received_hash = parsed.pop("hash", None)

    if not received_hash:
        raise HTTPException(
            status_code=401,
            detail="Telegram hash mavjud emas."
        )

    data_check_string = "\n".join(
        f"{key}={parsed[key]}"
        for key in sorted(parsed)
    )

    secret_key = hmac.new(
        b"WebAppData",
        settings.BOT_TOKEN.encode(),
        sha256,
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        sha256,
    ).hexdigest()

    if not compare_digest(calculated_hash, received_hash):
        raise HTTPException(
            status_code=401,
            detail="Telegram autentifikatsiyasi muvaffaqiyatsiz."
        )

    user_data = parsed.get("user")

    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="Telegram foydalanuvchisi topilmadi."
        )

    try:
        telegram_user = json.loads(user_data)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Telegram user ma'lumotlari noto'g'ri."
        )

    telegram_id = telegram_user.get("id")

    if not telegram_id:
        raise HTTPException(
            status_code=401,
            detail="Telegram ID topilmadi."
        )

    return telegram_user


def get_authenticated_user(db: Session, init_data: str):
    telegram_user = validate_telegram_init_data(init_data)
    telegram_id = int(telegram_user["id"])

    user = get_user_by_telegram_id(db, telegram_id)

    if not user:
        user = User(
            telegram_id=telegram_id,
            username=telegram_user.get("username"),
            first_name=telegram_user.get("first_name"),
            blocked=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.username = telegram_user.get("username")
        user.first_name = telegram_user.get("first_name")
        db.commit()

    if user.blocked:
        raise HTTPException(
            status_code=403,
            detail="Sizning profilingiz bloklangan."
        )

    return user


def require_admin(user: User):
    if user.telegram_id not in settings.admin_ids:
        raise HTTPException(
            status_code=403,
            detail="Admin huquqi talab qilinadi."
        )
    return user


@app.post("/api/auth/telegram")
def telegram_auth(
    init_data: str,
    db: Session = Depends(get_db)
):
    user = get_authenticated_user(db, init_data)

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "blocked": user.blocked,
    }


@app.get("/api/leagues")
def get_leagues(db: Session = Depends(get_db)):
    leagues = db.scalars(
        select(League)
        .where(League.active.is_(True))
        .order_by(League.id)
    ).all()

    result = []

    for league in leagues:
        season = db.scalar(
            select(Season)
            .where(
                Season.league_id == league.id,
                Season.active.is_(True)
            )
            .order_by(Season.id.desc())
        )

        result.append({
            "id": league.id,
            "name": league.name,
            "country": league.country,
            "active": league.active,
            "active_season": (
                {
                    "id": season.id,
                    "name": season.name,
                    "deadline_hour": season.deadline_hour,
                    "deadline_minute": season.deadline_minute,
                }
                if season else None
            )
        })

    return result


@app.get("/api/seasons")
def get_seasons(
    league_id: int,
    db: Session = Depends(get_db)
):
    seasons = db.scalars(
        select(Season)
        .where(Season.league_id == league_id)
        .order_by(Season.id.desc())
    ).all()

    return [
        {
            "id": season.id,
            "league_id": season.league_id,
            "name": season.name,
            "active": season.active,
            "deadline_hour": season.deadline_hour,
            "deadline_minute": season.deadline_minute,
        }
        for season in seasons
    ]


@app.get("/api/seasons/{season_id}")
def get_season(
    season_id: int,
    db: Session = Depends(get_db)
):
    season = db.get(Season, season_id)

    if not season:
        raise HTTPException(
            status_code=404,
            detail="Mavsum topilmadi."
        )

    return {
        "id": season.id,
        "league_id": season.league_id,
        "name": season.name,
        "active": season.active,
        "deadline_hour": season.deadline_hour,
        "deadline_minute": season.deadline_minute,
    }


@app.get("/api/teams")
def get_teams(
    league: str | None = None,
    season_id: int | None = None,
    db: Session = Depends(get_db)
):
    query = (
        select(Team)
        .join(Season, Team.season_id == Season.id)
        .join(League, Season.league_id == League.id)
    )

    if league:
        query = query.where(League.name == league)

    if season_id:
        query = query.where(Team.season_id == season_id)

    teams = db.scalars(
        query.order_by(Team.name)
    ).all()

    return [
        {
            "id": team.id,
            "season_id": team.season_id,
            "name": team.name,
            "short_name": team.short_name,
            "logo_url": team.logo_url,
            "participant_id": team.participant_id,
            "blocked": team.blocked,
            "available": (
                team.participant_id is None
                and not team.blocked
            ),
        }
        for team in teams
    ]


@app.post("/api/teams/{team_id}/select")
def select_team(
    team_id: int,
    init_data: str,
    db: Session = Depends(get_db)
):
    user = get_authenticated_user(db, init_data)

    team = db.get(Team, team_id)

    if not team:
        raise HTTPException(
            status_code=404,
            detail="Jamoa topilmadi."
        )

    if team.blocked:
        raise HTTPException(
            status_code=400,
            detail="Bu jamoa bloklangan."
        )

    season = db.get(Season, team.season_id)

    if not season or not season.active:
        raise HTTPException(
            status_code=400,
            detail="Bu mavsum faol emas."
        )

    existing_team = db.scalar(
        select(Team).where(
            Team.season_id == team.season_id,
            Team.participant_id == user.id
        )
    )

    if existing_team:
        raise HTTPException(
            status_code=400,
            detail="Siz bu mavsumda allaqachon jamoa tanlagansiz."
        )

    if team.participant_id is not None:
        raise HTTPException(
            status_code=409,
            detail="Bu jamoani boshqa ishtirokchi tanlagan."
        )

    team.participant_id = user.id
    db.commit()
    db.refresh(team)

    return {
        "success": True,
        "message": "Jamoa muvaffaqiyatli tanlandi.",
        "team": {
            "id": team.id,
            "name": team.name,
            "short_name": team.short_name,
            "season_id": team.season_id,
        }
    }


@app.get("/api/my-team")
def my_team(
    season_id: int,
    init_data: str,
    db: Session = Depends(get_db)
):
    user = get_authenticated_user(db, init_data)

    team = get_user_team(db, user.id, season_id)

    if not team:
        return {"team": None}

    return {
        "team": {
            "id": team.id,
            "name": team.name,
            "short_name": team.short_name,
            "logo_url": team.logo_url,
            "season_id": team.season_id,
        }
    }


@app.get("/api/my-matches")
def my_matches(
    season_id: int,
    round_number: int | None = None,
    init_data: str = "",
    db: Session = Depends(get_db)
):
    user = get_authenticated_user(db, init_data)

    team = get_user_team(db, user.id, season_id)

    if not team:
        return []

    query = select(Match).where(
        Match.season_id == season_id,
        (
            (Match.home_team_id == team.id)
            | (Match.away_team_id == team.id)
        )
    )

    if round_number:
        query = query.where(
            Match.round_number == round_number
        )

    matches = db.scalars(
        query.order_by(
            Match.round_number,
            Match.id
        )
    ).all()

    result = []

    for match in matches:
        home_team = db.get(Team, match.home_team_id)
        away_team = db.get(Team, match.away_team_id)

        existing_result = db.scalar(
            select(Result).where(
                Result.match_id == match.id
            )
        )

        result.append({
            "id": match.id,
            "round_number": match.round_number,
            "home_team_id": match.home_team_id,
            "away_team_id": match.away_team_id,
            "home_team_name": (
                home_team.name if home_team else None
            ),
            "away_team_name": (
                away_team.name if away_team else None
            ),
            "status": match.status,
            "deadline": match.deadline,
            "result": (
                {
                    "id": existing_result.id,
                    "home_goals": existing_result.home_goals,
                    "away_goals": existing_result.away_goals,
                    "submitted_by": existing_result.submitted_by,
                    "confirmed_by": existing_result.confirmed_by,
                    "submitted_at": existing_result.submitted_at,
                    "confirmed_at": existing_result.confirmed_at,
                }
                if existing_result else None
            )
        })

    return result


@app.get("/api/round/{round_number}")
def get_round(
    round_number: int,
    season_id: int,
    db: Session = Depends(get_db)
):
    if round_number < 1 or round_number > 38:
        raise HTTPException(
            status_code=400,
            detail="Tur raqami 1 dan 38 gacha bo'lishi kerak."
        )

    matches = db.scalars(
        select(Match)
        .where(
            Match.season_id == season_id,
            Match.round_number == round_number
        )
        .order_by(Match.id)
    ).all()

    result = []

    for match in matches:
        home_team = db.get(Team, match.home_team_id)
        away_team = db.get(Team, match.away_team_id)

        existing_result = db.scalar(
            select(Result).where(
                Result.match_id == match.id
            )
        )

        result.append({
            "id": match.id,
            "round_number": match.round_number,
            "home_team": (
                home_team.name if home_team else None
            ),
            "away_team": (
                away_team.name if away_team else None
            ),
            "home_team_id": match.home_team_id,
            "away_team_id": match.away_team_id,
            "status": match.status,
            "deadline": match.deadline,
            "result": (
                {
                    "home_goals": existing_result.home_goals,
                    "away_goals": existing_result.away_goals,
                    "confirmed": (
                        existing_result.confirmed_by is not None
                    ),
                }
                if existing_result else None
            )
        })

    return result


@app.post("/api/results")
def submit_result(
    data: ResultCreate,
    init_data: str,
    db: Session = Depends(get_db)
):
    user = get_authenticated_user(db, init_data)

    match = db.get(Match, data.match_id)

    if not match:
        raise HTTPException(
            status_code=404,
            detail="O'yin topilmadi."
        )

    allowed, error_message = can_submit_result(
        db,
        match,
        user.id
    )

    if not allowed:
        raise HTTPException(
            status_code=400,
            detail=error_message
        )

    home_team = db.get(Team, match.home_team_id)
    away_team = db.get(Team, match.away_team_id)

    if not home_team or not away_team:
        raise HTTPException(
            status_code=400,
            detail="O'yin jamoalari topilmadi."
        )

    home_participant = home_team.participant_id
    away_participant = away_team.participant_id

    if not home_participant or not away_participant:
        raise HTTPException(
            status_code=400,
            detail="Ikkala jamoada ham ishtirokchi bo'lishi kerak."
        )

    if user.id not in (
        home_participant,
        away_participant
    ):
        raise HTTPException(
            status_code=403,
            detail="Bu o'yinga sizda ruxsat yo'q."
        )

    existing_result = db.scalar(
        select(Result).where(
            Result.match_id == match.id
        )
    )

    if existing_result:
        raise HTTPException(
            status_code=409,
            detail="Bu o'yin uchun natija allaqachon yuborilgan."
        )

    result = Result(
        match_id=match.id,
        submitted_by=user.id,
        home_goals=data.home_goals,
        away_goals=data.away_goals,
    )

    db.add(result)
    match.status = "pending_confirmation"

    db.commit()
    db.refresh(result)

    return {
        "success": True,
        "message": "Natija yuborildi. Raqib tasdig'i kutilmoqda.",
        "result": {
            "id": result.id,
            "match_id": result.match_id,
            "home_goals": result.home_goals,
            "away_goals": result.away_goals,
            "submitted_by": result.submitted_by,
            "confirmed_by": result.confirmed_by,
        }
    }


@app.post("/api/results/{result_id}/confirm")
def confirm_result(
    result_id: int,
    init_data: str,
    db: Session = Depends(get_db)
):
    user = get_authenticated_user(db, init_data)

    result = db.get(Result, result_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Natija topilmadi."
        )

    if result.confirmed_by:
        raise HTTPException(
            status_code=400,
            detail="Bu natija allaqachon tasdiqlangan."
        )

    if result.submitted_by == user.id:
        raise HTTPException(
            status_code=400,
            detail="O'zingiz yuborgan natijani tasdiqlay olmaysiz."
        )

    match = db.get(Match, result.match_id)

    if not match:
        raise HTTPException(
            status_code=404,
            detail="O'yin topilmadi."
        )

    participant_ids = get_match_participant_ids(
        db,
        match
    )

    if user.id not in participant_ids:
        raise HTTPException(
            status_code=403,
            detail="Siz bu o'yin ishtirokchisi emassiz."
        )

    result.confirmed_by = user.id
    result.confirmed_at = datetime.utcnow()
    match.status = "confirmed"

    db.commit()
    db.refresh(result)

    return {
        "success": True,
        "message": "Natija tasdiqlandi.",
        "result": {
            "id": result.id,
            "match_id": result.match_id,
            "home_goals": result.home_goals,
            "away_goals": result.away_goals,
            "confirmed_by": result.confirmed_by,
            "confirmed_at": result.confirmed_at,
        }
    }


@app.post("/api/results/{result_id}/reject")
def reject_result(
    result_id: int,
    init_data: str,
    db: Session = Depends(get_db)
):
    user = get_authenticated_user(db, init_data)

    result = db.get(Result, result_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Natija topilmadi."
        )

    if result.confirmed_by:
        raise HTTPException(
            status_code=400,
            detail="Tasdiqlangan natijani rad etib bo'lmaydi."
        )

    if result.submitted_by == user.id:
        raise HTTPException(
            status_code=400,
            detail="O'zingiz yuborgan natijani rad eta olmaysiz."
        )

    match = db.get(Match, result.match_id)

    if not match:
        raise HTTPException(
            status_code=404,
            detail="O'yin topilmadi."
        )

    participant_ids = get_match_participant_ids(
        db,
        match
    )

    if user.id not in participant_ids:
        raise HTTPException(
            status_code=403,
            detail="Siz bu o'yin ishtirokchisi emassiz."
        )

    match.status = "disputed"
    db.commit()

    return {
        "success": True,
        "message": "Natija rad etildi. Admin ko'rib chiqishi kerak.",
        "status": "disputed",
    }


@app.get("/api/standings")
def standings(
    season_id: int,
    db: Session = Depends(get_db)
):
    season = db.get(Season, season_id)

    if not season:
        raise HTTPException(
            status_code=404,
            detail="Mavsum topilmadi."
        )

    return calculate_standings(
        db,
        season_id
    )


@app.get("/api/messages")
def get_messages(
    init_data: str,
    recipient_id: int | None = None,
    db: Session = Depends(get_db)
):
    user = get_authenticated_user(db, init_data)

    if recipient_id is None:
        messages = db.scalars(
            select(Message)
            .where(
                Message.recipient_id.is_(None),
                Message.deleted.is_(False)
            )
            .order_by(Message.created_at)
        ).all()
    else:
        other_user = db.get(User, recipient_id)

        if not other_user:
            raise HTTPException(
                status_code=404,
                detail="Foydalanuvchi topilmadi."
            )

        messages = db.scalars(
            select(Message)
            .where(
                Message.deleted.is_(False),
                (
                    (
                        (Message.sender_id == user.id)
                        &
                        (Message.recipient_id == recipient_id)
                    )
                    |
                    (
                        (Message.sender_id == recipient_id)
                        &
                        (Message.recipient_id == user.id)
                    )
                )
            )
            .order_by(Message.created_at)
        ).all()

    return [
        {
            "id": message.id,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "text": message.text,
            "created_at": message.created_at,
            "deleted": message.deleted,
        }
        for message in messages
    ]


@app.post("/api/messages")
def send_message(
    data: MessageCreate,
    init_data: str,
    db: Session = Depends(get_db)
):
    user = get_authenticated_user(db, init_data)

    if data.recipient_id == user.id:
        raise HTTPException(
            status_code=400,
            detail="O'zingizga xabar yubora olmaysiz."
        )

    if data.recipient_id is not None:
        recipient = db.get(User, data.recipient_id)

        if not recipient:
            raise HTTPException(
                status_code=404,
                detail="Qabul qiluvchi foydalanuvchi topilmadi."
            )

        if recipient.blocked:
            raise HTTPException(
                status_code=400,
                detail="Bu foydalanuvchi bloklangan."
            )

    message = Message(
        sender_id=user.id,
        recipient_id=data.recipient_id,
        text=data.text.strip(),
        deleted=False,
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
            "created_at": message.created_at,
            "deleted": message.deleted,
        }
    }


@app.get("/api/admin/check")
def admin_check(
    init_data: str,
    db: Session = Depends(get_db)
):
    user = get_authenticated_user(db, init_data)
    require_admin(user)

    return {
        "admin": True,
        "telegram_id": user.telegram_id,
    }


@app.get("/api/admin/dashboard")
def admin_dashboard(
    init_data: str,
    db: Session = Depends(get_db)
):
    user = get_authenticated_user(db, init_data)
    require_admin(user)

    total_users = len(
        db.scalars(select(User)).all()
    )

    total_teams = len(
        db.scalars(select(Team)).all()
    )

    total_matches = len(
        db.scalars(select(Match)).all()
    )

    pending_results = len(
        db.scalars(
            select(Result)
            .join(Match, Result.match_id == Match.id)
            .where(
                Match.status == "pending_confirmation"
            )
        ).all()
    )

    disputed_results = len(
        db.scalars(
            select(Result)
            .join(Match, Result.match_id == Match.id)
            .where(
                Match.status == "disputed"
            )
        ).all()
    )

    return {
        "users": total_users,
        "teams": total_teams,
        "matches": total_matches,
        "pending_results": pending_results,
        "disputed_results": disputed_results,
    }


@app.get("/api/admin/users")
def admin_users(
    init_data: str,
    db: Session = Depends(get_db)
):
    user = get_authenticated_user(db, init_data)
    require_admin(user)

    users = db.scalars(
        select(User).order_by(User.id.desc())
    ).all()

    return [
        {
            "id": item.id,
            "telegram_id": item.telegram_id,
            "username": item.username,
            "first_name": item.first_name,
            "blocked": item.blocked,
            "is_admin": (
                item.telegram_id in settings.admin_ids
            ),
        }
        for item in users
    ]


@app.post("/api/admin/users/{user_id}/block")
def admin_block_user(
    user_id: int,
    init_data: str,
    db: Session = Depends(get_db)
):
    admin = get_authenticated_user(db, init_data)
    require_admin(admin)

    target = db.get(User, user_id)

    if not target:
        raise HTTPException(
            status_code=404,
            detail="Foydalanuvchi topilmadi."
        )

    if target.telegram_id in settings.admin_ids:
        raise HTTPException(
            status_code=400,
            detail="Admin foydalanuvchini bloklab bo'lmaydi."
        )

    target.blocked = True
    db.commit()

    return {
        "success": True,
        "message": "Foydalanuvchi bloklandi."
    }


@app.post("/api/admin/users/{user_id}/unblock")
def admin_unblock_user(
    user_id: int,
    init_data: str,
    db: Session = Depends(get_db)
):
    admin = get_authenticated_user(db, init_data)
    require_admin(admin)

    target = db.get(User, user_id)

    if not target:
        raise HTTPException(
            status_code=404,
            detail="Foydalanuvchi topilmadi."
        )

    target.blocked = False
    db.commit()

    return {
        "success": True,
        "message": "Foydalanuvchi blokdan chiqarildi."
    }


@app.get("/api/admin/disputes")
def admin_disputes(
    init_data: str,
    db: Session = Depends(get_db)
):
    admin = get_authenticated_user(db, init_data)
    require_admin(admin)

    results = db.scalars(
        select(Result)
        .join(Match, Result.match_id == Match.id)
        .where(Match.status == "disputed")
        .order_by(Result.submitted_at.desc())
    ).all()

    response = []

    for result in results:
        match = db.get(Match, result.match_id)

        if not match:
            continue

        home_team = db.get(Team, match.home_team_id)
        away_team = db.get(Team, match.away_team_id)

        response.append({
            "result_id": result.id,
            "match_id": match.id,
            "round_number": match.round_number,
            "home_team": (
                home_team.name if home_team else None
            ),
            "away_team": (
                away_team.name if away_team else None
            ),
            "home_goals": result.home_goals,
            "away_goals": result.away_goals,
            "submitted_by": result.submitted_by,
            "submitted_at": result.submitted_at,
        })

    return response


@app.post("/api/admin/results/{result_id}/confirm")
def admin_confirm_result(
    result_id: int,
    init_data: str,
    db: Session = Depends(get_db)
):
    admin = get_authenticated_user(db, init_data)
    require_admin(admin)

    result = db.get(Result, result_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Natija topilmadi."
        )

    match = db.get(Match, result.match_id)

    if not match:
        raise HTTPException(
            status_code=404,
            detail="O'yin topilmadi."
        )

    if result.confirmed_by is None:
        result.confirmed_by = admin.id
        result.confirmed_at = datetime.utcnow()

    match.status = "confirmed"
    db.commit()

    return {
        "success": True,
        "message": "Natija admin tomonidan tasdiqlandi."
    }


@app.delete("/api/admin/messages/{message_id}")
def admin_delete_message(
    message_id: int,
    init_data: str,
    db: Session = Depends(get_db)
):
    admin = get_authenticated_user(db, init_data)
    require_admin(admin)

    message = db.get(Message, message_id)

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Xabar topilmadi."
        )

    message.deleted = True
    db.commit()

    return {
        "success": True,
        "message": "Xabar o'chirildi."
    }


@app.post("/api/admin/seasons/{season_id}/check")
def admin_check_season(
    season_id: int,
    init_data: str,
    db: Session = Depends(get_db)
):
    admin = get_authenticated_user(db, init_data)
    require_admin(admin)

    next_season = check_and_start_next_season(
        db,
        season_id
    )

    if not next_season:
        return {
            "success": False,
            "message": (
                "Mavsum hali tugamagan yoki faol emas."
            )
        }

    return {
        "success": True,
        "message": "Keyingi mavsum ishga tushirildi.",
        "season": {
            "id": next_season.id,
            "name": next_season.name,
            "league_id": next_season.league_id,
        }
    }
