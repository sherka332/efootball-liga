from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import User


async def send_message_to_user(
    bot: Bot,
    db: Session,
    user_id: int,
    text: str
):
    """
    User ID orqali Telegram foydalanuvchisiga xabar yuboradi.
    """

    user = db.get(User, user_id)

 if not user:
        return False

    if user.blocked:
        return False

    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text=text
        )
        return True

    except Exception:
        return False

async def send_message_to_telegram_id(
    bot: Bot,
    telegram_id: int,
    text: str
):
    """
    Telegram ID orqali to'g'ridan-to'g'ri xabar yuboradi.

    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=text
        )
        return True

    except Exception:
        return False


async def notify_result_submitted(
    bot: Bot,
    db: Session,
    opponent_user_id: int,
    home_team_name: str,
    away_team_name: str,
    home_goals: int,
    away_goals: int
):
"""
    Natija yuborilganda raqibga xabar yuboradi.
    """

    text = (
        "⚽ Yangi natija yuborildi!\n\n"
        f"🏠 {home_team_name}  {home_goals}:{away_goals}  "
        f"{away_team_name}\n\n"
        "Natijani tekshirib, tasdiqlang yoki rad eting."
    )

    return await send_message_to_user(
        bot,
        db,
        opponent_user_id,
        text
    )

    async def notify_result_confirmed(
    bot: Bot,
    db: Session,
    user_id: int,
    home_team_name: str,
    away_team_name: str,
    home_goals: int,
    away_goals: int
):
    """
    Natija tasdiqlanganda xabar yuboradi.
    """

    text = (
        "✅ Natija tasdiqlandi!\n\n"
        f"🏠 {home_team_name}  {home_goals}:{away_goals}  "
        f"{away_team_name}\n\n"
        "Natija liga jadvaliga qo'shildi."
    )

    return await send_message_to_user(
        bot,
        db,
        user_id,
        text
    )

async def notify_result_rejected(
    bot: Bot,
    db: Session,
    user_id: int,
    home_team_name: str,
    away_team_name: str,
    home_goals: int,
    away_goals: int
):
    """
    Natija rad etilganda xabar yuboradi.
    """

    text = (
        "❌ Natija rad etildi!\n\n"
        f"🏠 {home_team_name}  {home_goals}:{away_goals}  "
        f"{away_team_name}\n\n"
        "Natija admin tomonidan ko'rib chiqiladi."
    )


return await send_message_to_user(
        bot,
        db,
        user_id,
        text
    )


async def notify_deadline_reminder(
    bot: Bot,
    db: Session,
    user_id: int,
    remaining_text: str
):
    """
    Deadline yaqinlashganda eslatma yuboradi.
    """

    text = (
        "⏰ Eslatma!\n\n"
        f"Natija topshirish uchun {remaining_text} qoldi.\n\n"
        "Bugungi o'yinlaringizni vaqtida yakunlang."
    )

return await send_message_to_user(
        bot,
        db,
        user_id,
        text
    )


async def notify_deadline_closed(
    bot: Bot,
    db: Session,
    user_id: int
):
    """
    23:30 da natija topshirish yopilganda xabar.

    """

    text = (
        "🔒 Bugungi natija topshirish vaqti tugadi.\n\n"
        "⏰ Deadline: 23:30\n\n"
        "Keyingi imkoniyatni admin belgilashi mumkin."
    )

    return await send_message_to_user(
        bot,
        db,
        user_id,
        text
    )

async def notify_new_season(
    bot: Bot,
    db: Session,
    user_id: int,
    season_name: str
):
    """
    Yangi mavsum boshlanganda xabar yuboradi.
    """

    text = (
        "🏆 Yangi mavsum boshlandi!\n\n"
        f"🔥 {season_name}\n\n"
        "Yangi mavsumda jamoangizni tanlang "
        "va o'yinlarni boshlang."
    )

    return await send_message_to_user(
        bot,
        db,
        user_id,
        text
    )

async def notify_admins(
    bot: Bot,
    text: str
):
    """
    Barcha adminlarga Telegram xabari yuboradi.
    """

    success_count = 0

    for telegram_id in settings.admin_ids:

      try:
            await bot.send_message(
                chat_id=telegram_id,
                text=text
            )

            success_count += 1

        except Exception:
            continue

    return success_count


async def notify_dispute_to_admins(
    bot: Bot,
    match_id: int,
    home_team_name: str,
    away_team_name: str
):
 """
    Natija rad etilganda adminlarga xabar beradi.
    """

    text = (
        "🚨 Natija bo'yicha nizo!\n\n"
        f"⚽ {home_team_name} - {away_team_name}\n"
        f"🆔 Match ID: {match_id}\n\n"
        "Admin panel orqali tekshirish kerak."
    )

    return await notify_admins(
        bot,
        text
    )
  
