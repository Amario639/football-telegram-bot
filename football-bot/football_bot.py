import os
import requests
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
API_KEY = os.environ["API_KEY"]
YOUR_TELEGRAM_USER_ID = int(os.environ["USER_ID"])

headers = {"x-apisports-key": API_KEY}

def get_today_fixtures():
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    url = f"https://v3.football.api-sports.io/fixtures?date={today}"
    res = requests.get(url, headers=headers).json()
    return res.get("response", [])

def get_team_goals(team_id, league_id, season):
    url = f"https://v3.football.api-sports.io/teams/statistics?team={team_id}&season={season}&league={league_id}"
    res = requests.get(url, headers=headers).json()
    stats = res.get("response", {})
    if stats:
        goals = stats["goals"]["for"]["average"]["total"]
        return float(goals) if goals else 1.0
    return 1.0

def estimate_over_25(home_gpg, away_gpg):
    avg = home_gpg + away_gpg
    if avg >= 3.0:
        return f"{avg:.1f} goals — 🔥 Very Likely"
    elif avg >= 2.5:
        return f"{avg:.1f} goals — ✅ Likely"
    else:
        return f"{avg:.1f} goals — ❌ Unlikely"

def build_daily_message():
    fixtures = get_today_fixtures()
    message = f"📊 *Today's Over 2.5 Predictions*\n\n"
    count = 0
    for game in fixtures:
        try:
            league_id = game["league"]["id"]
            season = game["league"]["season"]
            home = game["teams"]["home"]
            away = game["teams"]["away"]
            home_gpg = get_team_goals(home["id"], league_id, season)
            away_gpg = get_team_goals(away["id"], league_id, season)
            over25 = estimate_over_25(home_gpg, away_gpg)
            message += f"⚽ {home['name']} vs {away['name']}\n   {over25}\n\n"
            count += 1
            if count >= 10:
                break
        except:
            continue
    if count == 0:
        message += "No matches found today."
    return message

async def send_daily_message(application):
    message = build_daily_message()
    await application.bot.send_message(chat_id=YOUR_TELEGRAM_USER_ID, text=message, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running. You'll get daily stats at 12 PM.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your chat ID is: {update.effective_chat.id}")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_id))

    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: asyncio.run(send_daily_message(app)), 'cron', hour=12, minute=0)
    scheduler.start()

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
