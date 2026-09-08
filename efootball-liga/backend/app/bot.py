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
from .scheduler import scheduler_loop

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):

    if not settings.WEBAPP_URL:

        await message.answer(
            "⚠️ Mini App manzili sozlanmagan.\n\n"
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

name = (
        message.from_user.first_name
        if message.from_user
        else "Foydalanuvchi"
    )

    await message.answer(
        f"⚽ Salom, {name}!\n\n"
        "🇪🇸 La Liga\n"
        "🏴 Premier League\n\n"
        "eFootball Liga musobaqasiga "
        "xush kelibsiz!\n\n"
        "Jamoangizni tanlang va "
        "o'yinlarni boshlang.",
        reply_markup=keyboard
    )

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

    print(
        "🤖 Telegram bot ishga tushdi..."
    )

scheduler_task = asyncio.create_task(
        scheduler_loop(bot)
    )

    try:

        await dp.start_polling(bot)

    finally:

        scheduler_task.cancel()

        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass

        await bot.session.close()


if name == "main":
    asyncio.run(main())
