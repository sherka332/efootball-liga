from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from .database import Base, engine, get_db
from .models import User, Season, SeasonPlayer, Match
from .schemas import RegisterIn, LoginIn, TelegramAuthIn, SeasonCreate, StatusIn, ScoreIn, UserOut
from .auth import hash_password, verify_password, make_token, current_user, require_admin
from .services import validate_telegram_init_data, sync_telegram_user, generate_round_robin
from .config import settings

app = FastAPI(title="eFootball Liga API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/api/health")
def health():
    return {"ok": True}

@app.post("/api/auth/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(400, "Username already exists")
    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"token": make_token(user), "user": UserOut.model_validate(user)}

@app.post("/api/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    if user.is_banned:
        raise HTTPException(403, "User is banned")
    return {"token": make_token(user), "user": UserOut.model_validate(user)}

@app.post("/api/auth/telegram")
def telegram_login(body: TelegramAuthIn, db: Session = Depends(get_db)):
    tg = validate_telegram_init_data(body.init_data)
    user = sync_telegram_user(db, tg)
    if user.is_banned:
        raise HTTPException(403, "User is banned")
    return {"token": make_token(user), "user": UserOut.model_validate(user)}

@app.get("/api/me")
def me(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    user = current_user(db, authorization)
    return UserOut.model_validate(user)

@app.get("/api/players")
def players(db: Session = Depends(get_db)):
    return [UserOut.model_validate(x) for x in db.query(User).order_by(User.id.desc()).all()]

@app.get("/api/seasons")
def seasons(db: Session = Depends(get_db)):
    return [{"id": s.id, "name": s.name, "status": s.status} for s in db.query(Season).order_by(Season.id.desc()).all()]

@app.post("/api/seasons")
def create_season(body: SeasonCreate, authorization: str = Header(default=""), db: Session = Depends(get_db)):
    admin = require_admin(current_user(db, authorization))
    s = Season(name=body.name)
    db.add(s); db.commit(); db.refresh(s)
    return {"id": s.id, "name": s.name, "status": s.status}

@app.post("/api/seasons/{season_id}/join")
def join_season(season_id: int, authorization: str = Header(default=""), db: Session = Depends(get_db)):
    user = current_user(db, authorization)
    season = db.get(Season, season_id)
    if not season or season.status != "OPEN":
        raise HTTPException(400, "Season is not open")
    if not db.query(SeasonPlayer).filter_by(season_id=season_id, user_id=user.id).first():
        db.add(SeasonPlayer(season_id=season_id, user_id=user.id)); db.commit()
    return {"ok": True}

@app.get("/api/seasons/{season_id}/players")
def season_players(season_id: int, db: Session = Depends(get_db)):
    rows = db.query(User).join(SeasonPlayer, SeasonPlayer.user_id == User.id).filter(SeasonPlayer.season_id == season_id).all()
    return [UserOut.model_validate(x) for x in rows]

@app.post("/api/seasons/{season_id}/generate")
def generate(season_id: int, authorization: str = Header(default=""), db: Session = Depends(get_db)):
    require_admin(current_user(db, authorization))
    generate_round_robin(db, season_id)
    return {"ok": True}

@app.get("/api/seasons/{season_id}/standings")
def standings(season_id: int, db: Session = Depends(get_db)):
    players = db.query(User).join(SeasonPlayer, SeasonPlayer.user_id == User.id).filter(SeasonPlayer.season_id == season_id).all()
    matches = db.query(Match).filter(Match.season_id == season_id, Match.played == True).all()
    stats = {u.id: {"user_id": u.id, "username": u.username, "played": 0, "win": 0, "draw": 0, "loss": 0, "gf": 0, "ga": 0, "gd": 0, "points": 0} for u in players}
    for m in matches:
        stats[m.home_user_id]["played"] += 1; stats[m.away_user_id]["played"] += 1
        stats[m.home_user_id]["gf"] += m.home_score; stats[m.home_user_id]["ga"] += m.away_score
        stats[m.away_user_id]["gf"] += m.away_score; stats[m.away_user_id]["ga"] += m.home_score
        if m.home_score > m.away_score:
            stats[m.home_user_id]["win"] += 1; stats[m.away_user_id]["loss"] += 1; stats[m.home_user_id]["points"] += 3
        elif m.home_score < m.away_score:
            stats[m.away_user_id]["win"] += 1; stats[m.home_user_id]["loss"] += 1; stats[m.away_user_id]["points"] += 3
        else:
            stats[m.home_user_id]["draw"] += 1; stats[m.away_user_id]["draw"] += 1
            stats[m.home_user_id]["points"] += 1; stats[m.away_user_id]["points"] += 1
    for x in stats.values():
        x["gd"] = x["gf"] - x["ga"]
    return sorted(stats.values(), key=lambda x: (x["points"], x["gd"], x["gf"]), reverse=True)

@app.get("/api/seasons/{season_id}/matches")
def matches(season_id: int, db: Session = Depends(get_db)):
    ms = db.query(Match).filter(Match.season_id == season_id).order_by(Match.round_number, Match.id).all()
    users = {u.id: u.username for u in db.query(User).all()}
    return [{"id": m.id, "round_number": m.round_number, "home_user_id": m.home_user_id, "away_user_id": m.away_user_id,
             "home": users.get(m.home_user_id), "away": users.get(m.away_user_id),
             "home_score": m.home_score, "away_score": m.away_score, "played": m.played} for m in ms]

@app.post("/api/matches/{match_id}/score")
def score(match_id: int, body: ScoreIn, authorization: str = Header(default=""), db: Session = Depends(get_db)):
    require_admin(current_user(db, authorization))
    m = db.get(Match, match_id)
    if not m: raise HTTPException(404, "Match not found")
    m.home_score = body.home_score; m.away_score = body.away_score; m.played = True
    db.commit()
    return {"ok": True}

@app.delete("/api/matches/{match_id}")
def delete_match(match_id: int, authorization: str = Header(default=""), db: Session = Depends(get_db)):
    require_admin(current_user(db, authorization))
    m = db.get(Match, match_id)
    if not m: raise HTTPException(404, "Match not found")
    db.delete(m); db.commit()
    return {"ok": True}

@app.post("/api/admin/players/{user_id}/status")
def player_status(user_id: int, body: StatusIn, authorization: str = Header(default=""), db: Session = Depends(get_db)):
    require_admin(current_user(db, authorization))
    user = db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    user.is_banned = body.status.upper() == "BANNED"
    db.commit()
    return {"ok": True}

@app.post("/api/admin/seasons/{season_id}/status")
def season_status(season_id: int, body: StatusIn, authorization: str = Header(default=""), db: Session = Depends(get_db)):
    require_admin(current_user(db, authorization))
    s = db.get(Season, season_id)
    if not s: raise HTTPException(404, "Season not found")
    s.status = body.status.upper()
    db.commit()
    return {"ok": True}

@app.delete("/api/admin/seasons/{season_id}")
def delete_season(season_id: int, authorization: str = Header(default=""), db: Session = Depends(get_db)):
    require_admin(current_user(db, authorization))
    s = db.get(Season, season_id)
    if not s: raise HTTPException(404, "Season not found")
    db.query(Match).filter(Match.season_id == season_id).delete()
    db.query(SeasonPlayer).filter(SeasonPlayer.season_id == season_id).delete()
    db.delete(s); db.commit()
    return {"ok": True}
