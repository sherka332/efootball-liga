import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal
from .models import Match, Season, Team
from .notifications import (
    notify_deadline_closed,
    notify_deadline_reminder,
)
from .season_manager import check_and_start_next_season


TIMEZONE = ZoneInfo(settings.TIMEZONE)


def get_today_matches(
    db: Session
):
    """
    Bugungi o'yinlarni topadi.
    """

    now = datetime.now(TIMEZONE)

    start_of_day = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

end_of_day = now.replace(
        hour=23,
        minute=59,
        second=59,
        microsecond=999999
    )

    return db.scalars(
        select(Match)
        .where(
            Match.deadline >= start_of_day,
            Match.deadline <= end_of_day
        )
        .order_by(
            Match.round_number,
            Match.id
        )
    ).all()

def get_match_participants(
    db: Session,
    match: Match
):
    """
    Matchdagi ikkala qatnashchini topadi.
    """

    home_team = db.get(
        Team,
        match.home_team_id
    )

away_team = db.get(
        Team,
        match.away_team_id
    )

    if not home_team or not away_team:
        return []

    participants = []

    if home_team.participant_id:
        participants.append(
            home_team.participant_id
        )

if away_team.participant_id:
        participants.append(
            away_team.participant_id
        )

    return list(set(participants))


async def send_reminder(
    bot: Bot,
    reminder_type: str
):
   """
    Bugungi o'yinlar uchun eslatma yuboradi.
    """

    db: Session = SessionLocal()

    try:
        matches = get_today_matches(db)

        notified_users = set()

        for match in matches:

            if match.status in (
                "completed",
                "confirmed"
            ):
              continue

            participants = get_match_participants(
                db,
                match
            )

            for user_id in participants:

                if user_id in notified_users:
                    continue

                if reminder_type == "20:00":
                    remaining_text = "3 soat 30 daqiqa"

                elif reminder_type == "22:30":
                    remaining_text = "1 soat"

                elif reminder_type == "23:00":
                    remaining_text = "30 daqiqa"
                  else:
                    remaining_text = "oz vaqt"

                await notify_deadline_reminder(
                    bot,
                    db,
                    user_id,
                    remaining_text
                )

                notified_users.add(user_id)

finally:
        db.close()


async def close_today_results(
    bot: Bot
):
    """
    23:30 da bugungi o'yinlarni yopadi.
    """

    db: Session = SessionLocal()

    try:
        matches = get_today_matches(db)

        notified_users = set()

        for match in matches:

            if match.status in (
                "confirmed",
                "completed"
            ):
              continue

            match.status = "closed"

            participants = get_match_participants(
                db,
                match
            )

            for user_id in participants:

                if user_id in notified_users:
                    continue

                await notify_deadline_closed(
                    bot,
                    db,
                    user_id
                )
              notified_users.add(user_id)

        db.commit()

    finally:
        db.close()


async def check_seasons():
    """
    Tugagan mavsumlarni tekshiradi
    va keyingi mavsumni yaratadi.
    """

    db: Session = SessionLocal()

    try:
      active_seasons = db.scalars(
            select(Season)
            .where(
                Season.active.is_(True)
            )
        ).all()

        for season in active_seasons:

            try:
                check_and_start_next_season(
                    db,
                    season.id
                )

            except Exception as error:
                print(
                    f"Season error "
                    f"(season={season.id}): {error}"
                )
              db.rollback()

    finally:
        db.close()


async def scheduler_loop(
    bot: Bot
):
    """
    Asosiy avtomatik scheduler.

    Har daqiqada vaqtni tekshiradi.
    """

    last_20 = None
    last_2230 = None
    last_23 = None
    last_2330 = None
    last_season_check = None
  
while True:

        now = datetime.now(TIMEZONE)

        current_date = now.date()

        current_hour = now.hour
        current_minute = now.minute

        if (
            current_hour == 20
            and current_minute == 0
            and last_20 != current_date
        ):

          await send_reminder(
                bot,
                "20:00"
            )

            last_20 = current_date

        if (
            current_hour == 22
            and current_minute == 30
            and last_2230 != current_date
        ):
            await send_reminder(
                bot,
                "22:30"
            )

last_20 = current_date

        if (
            current_hour == 22
            and current_minute == 30
            and last_2230 != current_date
        ):
            await send_reminder(
                bot,
                "22:30"
            )

last_2230 = current_date

        if (
            current_hour == 23
            and current_minute == 0
            and last_23 != current_date
        ):
            await send_reminder(
                bot,
                "23:00"
            )

            last_23 = current_date

        if (
            current_hour == 23
            and current_minute == 30
            and last_2330 != current_date
        ):
          await close_today_results(bot)

            last_2330 = current_date

        if (
            last_season_check != current_date
            and current_hour >= 23
            and current_minute >= 30
        ):
            await check_seasons()

            last_season_check = current_date

        await asyncio.sleep(30)
        
