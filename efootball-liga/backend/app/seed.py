from .database import Base, engine, SessionLocal
from .models import User
from .auth import hash_password
from .config import settings

def seed():
    Base.metadata.create_all(bind=engine)
    if not settings.seed_admin:
        return
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == settings.admin_username).first()
        if not user:
            user = User(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
                role="ADMIN"
            )
            db.add(user)
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
