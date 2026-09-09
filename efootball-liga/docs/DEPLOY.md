# Render deployment

## 1. PostgreSQL
Create a Render PostgreSQL database and copy its internal connection string into the backend `DATABASE_URL`.

## 2. Backend
Create a Render Web Service:
- Root Directory: `backend`
- Build: `pip install -r requirements.txt`
- Start: `sh start.sh`

Environment:
- DATABASE_URL
- SECRET_KEY
- CORS_ORIGINS
- TELEGRAM_BOT_TOKEN
- TELEGRAM_ADMIN_ID
- SEED_ADMIN=false

`CORS_ORIGINS` should contain the deployed frontend/admin URLs separated by commas.

## 3. Frontend
Create a Render Static Site:
- Root Directory: `frontend`
- Build: `npm install && npm run build`
- Publish: `dist`

Environment:
- `VITE_API_URL=https://YOUR-BACKEND.onrender.com`

## 4. Admin
Create another Render Static Site:
- Root Directory: `admin`
- Build: `npm install && npm run build`
- Publish: `dist`
- `VITE_API_URL=https://YOUR-BACKEND.onrender.com`

## 5. Telegram
In BotFather configure the Mini App / Web App URL to the deployed frontend.

When the Mini App opens, Telegram supplies `initData`. The frontend sends it to `/api/auth/telegram`, and the backend validates it with `TELEGRAM_BOT_TOKEN`.

Set `TELEGRAM_ADMIN_ID` to the Telegram numeric ID of the administrator. The ID is compared only after Telegram's signature is validated.

Never commit `.env` or the bot token to GitHub.
