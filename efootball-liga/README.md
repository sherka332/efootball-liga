# eFootball Liga — Telegram Mini App

Full-stack eFootball league platform with:
- FastAPI backend
- React/Vite player Mini App
- React/Vite admin panel
- PostgreSQL support
- Telegram Mini App automatic authentication
- Server-side Telegram initData validation
- Automatic Telegram ID / username / name sync
- Telegram ID based admin recognition
- Seasons, joining, round-robin fixtures, standings and match results

## Telegram authentication

The Mini App sends `Telegram.WebApp.initData` to the backend. The backend validates the signature using the bot token and creates/updates the local user.

Set:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ADMIN_ID`

Do NOT trust a Telegram ID supplied directly by the browser.

Default local admin can also be seeded with:
- username: `admin`
- password: `admin123`

For production, change/remove the default admin and use Telegram admin authentication.

## Run backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Backend API: `http://localhost:8000`
Swagger: `http://localhost:8000/docs`

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL=http://localhost:8000` in `.env`.

## Telegram BotFather

Create/configure the Mini App URL in BotFather and point it to the deployed frontend URL.

For production:
- Backend: Render Web Service
- Frontend: Render Static Site
- Admin: Render Static Site
- Database: Render PostgreSQL

Set `VITE_API_URL` on both frontend and admin.
