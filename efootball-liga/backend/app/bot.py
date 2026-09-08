import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)

from .config import settings


router = Router()


# =========================================================
# /START
# =========================================================

@router.message(CommandStart())
async def start_handler(message: Message):

    if not settings.WEBAPP_URL:
        await message.answer(
            "⚠️ Mini App manzili sozlanmagan.\n"
            "WEBAPP_URL ni .env faylida kiriting."
        )
        return

keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏆 Ligaga kirish",
                    web_app=WebAppInfo(
                        url=settings.WEBAPP_URL
                    )
                )
            ]
        ]
)

name = message.from_user.first_name or "Foydalanuvchi"

    await message.answer(
        f"⚽ Salom, {name}!\n\n"
        "🇪🇸 La Liga\n"
        "🏴 Premier League\n\n"
        "eFootball Liga musobaqasiga xush kelibsiz!\n\n"
        "Jamoangizni tanlang va o'yinlarni boshlang.",
        reply_markup=keyboard
    )

# =========================================================
# BOT START
# =========================================================

async def main():

    if not settings.BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN .env faylida ko'rsatilmagan."
        )

bot = Bot(
        token=settings.BOT_TOKEN
    )

    dp = Dispatcher()

    dp.include_router(router)

    print("🤖 Telegram bot ishga tushdi...")

    await dp.start_polling(
        bot
    )

if __name__ == "__main__":
    asyncio.run(main())
