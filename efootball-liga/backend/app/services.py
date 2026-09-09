import hashlib, hmac, json, time
from urllib.parse import parse_qsl
from fastapi import HTTPException
from sqlalchemy.orm import Session
from .config import settings
from .models import User, SeasonPlayer, Match

def validate_telegram_init_data(init_data: str):
    if not settings.telegram_bot_token:
        raise HTTPException(500, "TELEGRAM_BOT_TOKEN is not configured")

    data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise HTTPException(401, "Telegram hash missing")

    auth_date = int(data.get("auth_date", "0"))
    if not auth_date or abs(time.time() - auth_date) > 86400:
        raise HTTPException(401, "Telegram initData expired")

    check_string = "\n".join(f"{k}={data[k]}" for k in sorted(data))
    secret_key = hmac.new(
        b"WebAppData",
        settings.telegram_bot_token.encode(),
        hashlib.sha256
    ).digest()
    calculated = hmac.new(
        secret_key,
        check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        raise HTTPException(401, "Invalid Telegram initData")

    user_raw = data.get("user")
    if not user_raw:
        raise HTTPException(401, "Telegram user missing")

    try:
        return json.loads(user_raw)
    except json.JSONDecodeError:
        raise HTTPException(401, "Invalid Telegram user data")

def sync_telegram_user(db: Session, tg: dict):
    telegram_id = str(tg["id"])
    username = tg.get("username")
    first_name = tg.get("first_name", "")
    last_name = tg.get("last_name", "")

    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user and username:
        user = db.query(User).filter(User.username == username).first()

    if not user:
        base = username or f"tg_{telegram_id}"
        candidate = base[:100]
        if db.query(User).filter(User.username == candidate).first():
            candidate = f"tg_{telegram_id}"
        user = User(username=candidate[:100], telegram_id=telegram_id)

    user.telegram_id = telegram_id
    user.telegram_username = username
    user.first_name = first_name
    user.last_name = last_name

    if settings.telegram_admin_id and telegram_id == str(settings.telegram_admin_id).strip():
        user.role = "ADMIN"

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def generate_round_robin(db: Session, season_id: int):
    players = [x.user_id for x in db.query(SeasonPlayer).filter(SeasonPlayer.season_id == season_id).all()]
    if len(players) < 2:
        raise HTTPException(400, "At least 2 players are required")

    old = db.query(Match).filter(Match.season_id == season_id).all()
    if old:
        raise HTTPException(400, "Fixtures already generated")

    if len(players) % 2:
        players.append(None)

    n = len(players)
    rounds = n - 1
    arr = players[:]

    for rnd in range(1, rounds + 1):
        for i in range(n // 2):
            a, b = arr[i], arr[n - 1 - i]
            if a is not None and b is not None:
                home, away = (a, b) if rnd % 2 else (b, a)
                db.add(Match(season_id=season_id, round_number=rnd,
                             home_user_id=home, away_user_id=away))
        arr = [arr[0]] + [arr[-1]] + arr[1:-1]
    db.commit()
