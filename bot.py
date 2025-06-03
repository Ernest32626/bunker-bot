import logging
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

TOKEN = "7613073856:AAHSG3ZJh36qcTZGtXQAbjg0qljd7r7tlw4"

logging.basicConfig(level=logging.INFO)

players = {}
game_started = False
situation = ""
revealed_cards = {}
votes = {}
roles = [
    "Хірург", "Інженер", "Вчитель", "Фермер", "Хімік", "Психолог", "Програміст", 
    "Пожежник", "Пілот", "Будівельник", "Шеф-кухар", "Ветеринар", "Фізик"
]
ages = list(range(18, 61))
health = ["Здорова людина", "Мається хронічна хвороба", "Одужує після травми", "Інвалідність", "ВІЛ-позитивний"]
hobbies = ["Гра на гітарі", "Виживання в дикій природі", "Малювання", "Бойові мистецтва", "Медитація"]
items = ["Аптечка", "Ніж", "Фільтр для води", "Радіоприймач", "Намет", "Консерви", "Запальничка", "Карти місцевості"]
situations = [
    "Зомбі апокаліпсис, 10 людей можуть вижити в бункері на 5 років.",
    "Ядерна війна — бункер вміщує лише 10 людей.",
    "Кліматична катастрофа — врятуватися можуть лише 10 людей у бункері.",
    "Світова пандемія — в бункер мають потрапити лише найкорисніші."
]

def generate_card():
    return {
        "Професія": random.choice(roles),
        "Вік": random.choice(ages),
        "Здоров'я": random.choice(health),
        "Хобі": random.choice(hobbies),
        "Предмет": random.choice(items)
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Я — бот гри Бункер. Напиши /join щоб увійти в гру.")

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, game_started
    if game_started:
        await update.message.reply_text("Гра вже почалася.")
        return

    user = update.effective_user
    if user.id not in players:
        players[user.id] = {
            "name": user.full_name,
            "card": generate_card(),
            "revealed": [],
            "voted": False
        }
        await update.message.reply_text("Тебе додано до гри.")
        await context.bot.send_message(chat_id=user.id, text=f"Твоя картка:\n" + "\n".join(
            f"{k}: {v}" for k, v in players[user.id]["card"].items()))
    else:
        await update.message.reply_text("Ти вже в грі.")

async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_started, situation
    if len(players) < 3:
        await update.message.reply_text("Для початку гри потрібно хоча б 3 гравці.")
        return

    game_started = True
    situation = random.choice(situations)
    await update.message.reply_text(f"Гру почато! Ситуація:\n\n{situation}\n\nВсі гравці отримали свої картки в особисті повідомлення. Починайте обговорення!")

async def reveal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not game_started or user.id not in players:
        await update.message.reply_text("Ти не в грі або гра ще не почалася.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Напиши, яку картку ти хочеш відкрити (наприклад: /reveal Вік)")
        return

    key = " ".join(args)
    card = players[user.id]["card"]

    if key not in card:
        await update.message.reply_text("Такої картки немає.")
        return

    if key in players[user.id]["revealed"]:
        await update.message.reply_text("Ти вже відкрив цю картку.")
        return

    players[user.id]["revealed"].append(key)
    text = f"{players[user.id]['name']} відкрив(ла) свою картку: {key} — {card[key]}"
    for pid in players:
        await context.bot.send_message(chat_id=pid, text=text)

async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not game_started or user.id not in players:
        await update.message.reply_text("Ти не в грі або гра ще не почалася.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Вкажи ім'я або ID гравця, за якого голосуєш (наприклад: /vote 12345678)")
        return

    try:
        target_id = int(args[0])
    except:
        await update.message.reply_text("Неправильний формат ID.")
        return

    if target_id not in players:
        await update.message.reply_text("Цього гравця немає.")
        return

    if players[user.id]["voted"]:
        await update.message.reply_text("Ти вже проголосував(ла).")
        return

    votes[target_id] = votes.get(target_id, 0) + 1
    players[user.id]["voted"] = True
    await update.message.reply_text("Голос зараховано.")

    total_votes = sum(votes.values())
    if total_votes == len(players):
        max_votes = max(votes.values())
        eliminated = [uid for uid, count in votes.items() if count == max_votes]
        if len(eliminated) == 1:
            eliminated_id = eliminated[0]
            name = players[eliminated_id]["name"]
            del players[eliminated_id]
            for pid in players:
                await context.bot.send_message(chat_id=pid, text=f"{name} було вигнано з бункера!")
        else:
            for pid in players:
                await context.bot.send_message(chat_id=pid, text="Нічия! Ніхто не вигнаний.")

        for pid in players:
            players[pid]["voted"] = False
        votes.clear()

        if len(players) == 2:
            names = [p["name"] for p in players.values()]
            for pid in players:
                await context.bot.send_message(chat_id=pid, text=f"Гру завершено!\nВижили: {', '.join(names)}")
            players.clear()
            global game_started
            game_started = False

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not game_started:
        await update.message.reply_text("Гра ще не почалася.")
        return
    text = f"Гравці у грі ({len(players)}):\n"
    for p in players.values():
        text += f"- {p['name']}\n"
    await update.message.reply_text(text)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("join", join))
app.add_handler(CommandHandler("startgame", startgame))
app.add_handler(CommandHandler("reveal", reveal))
app.add_handler(CommandHandler("vote", vote))
app.add_handler(CommandHandler("status", status))

app.run_polling()
