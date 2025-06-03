import random
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ParseMode

API_TOKEN = "7635553359:AAHKlFZ7h0F6CDuj676jpBhS6v_hLgJseOc"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

players = []
game_started = False
votes = {}
voted_users = set()
situation = ""
revealed = {}

# Дані
professions = ["Хірург", "Інженер", "Психолог", "Фермер", "Солдат", "Пілот", "Кухар"]
health = ["Здоровий", "Астма", "Рак 1 стадії", "Сліпий", "Інвалідність", "Глухий"]
hobbies = ["Йога", "Кулінарія", "Малювання", "Плавання"]
items = ["Аптечка", "Лопата", "Ніж", "Їжа на 7 днів"]
facts = ["Знає мови", "Має водійське", "Вижив в катастрофі"]
situations = ["Зомбі-апокаліпсис", "Ядерна війна", "Виверження супервулкану"]

def generate_card():
    return {
        "професія": random.choice(professions),
        "вік": random.randint(18, 65),
        "здоровʼя": random.choice(health),
        "хобі": random.choice(hobbies),
        "предмет": random.choice(items),
        "факт": random.choice(facts)
    }

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer("Привіт! Гра 'Бункер'.\n/join — приєднатися\n/startgame — почати гру")

@dp.message_handler(commands=["join"])
async def join_game(message: types.Message):
    global game_started
    if game_started:
        await message.reply("Гру вже розпочато.")
        return
    for p in players:
        if p["id"] == message.from_user.id:
            await message.reply("Ти вже в грі.")
            return
    card = generate_card()
    players.append({"id": message.from_user.id, "name": message.from_user.full_name, "card": card})
    revealed[message.from_user.id] = []
    await bot.send_message(
        message.from_user.id,
        f"🃏 Твоя картка:\n"
        f"Професія: {card['професія']}\n"
        f"Вік: {card['вік']}\n"
        f"Здоровʼя: {card['здоровʼя']}\n"
        f"Хобі: {card['хобі']}\n"
        f"Предмет: {card['предмет']}\n"
        f"Факт: {card['факт']}"
    )
    await message.answer(f"{message.from_user.full_name} приєднався до гри!")

@dp.message_handler(commands=["startgame"])
async def start_game(message: types.Message):
    global game_started, situation
    if game_started or len(players) < 3:
        await message.answer("Гра вже йде або замало гравців (мін. 3).")
        return
    game_started = True
    situation = random.choice(situations)
    await message.answer(f"🆘 Ситуація: {situation}")
    text = "\n".join([f"{p['name']} — {p['card']['професія']}" for p in players])
    await message.answer("🧾 Професії гравців:\n" + text)

@dp.message_handler(commands=["status"])
async def status(message: types.Message):
    if not game_started:
        await message.answer("Гра ще не почалась.")
        return
    text = "👥 Гравці у грі:\n" + "\n".join([p["name"] for p in players])
    await message.answer(text)

@dp.message_handler(commands=["reveal"])
async def reveal(message: types.Message):
    if not game_started:
        await message.answer("Гра ще не почалась.")
        return
    player = next((p for p in players if p["id"] == message.from_user.id), None)
    if not player:
        await message.answer("Тебе нема в грі.")
        return
    available = [k for k in player["card"] if k not in revealed[message.from_user.id] and k != "професія"]
    if not available:
        await message.answer("Ти вже відкрив усі частини картки.")
        return
    key = random.choice(available)
    value = player["card"][key]
    revealed[message.from_user.id].append(key)
    await message.answer(f"📢 {message.from_user.full_name} відкрив(ла): {key.capitalize()} — {value}")

@dp.message_handler(commands=["vote"])
async def vote(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Відповідай на повідомлення гравця.")
        return
    voter = message.from_user.id
    target = message.reply_to_message.from_user.id
    if voter == target:
        await message.reply("Не можна голосувати за себе.")
        return
    if voter in voted_users:
        await message.reply("Ти вже голосував.")
        return
    voted_users.add(voter)
    votes[target] = votes.get(target, 0) + 1
    await message.reply("Голос зараховано.")

    if len(voted_users) >= len(players):
        eliminated_id = max(votes, key=votes.get)
        eliminated_player = next((p for p in players if p["id"] == eliminated_id), None)
        if eliminated_player:
            players.remove(eliminated_player)
            await message.answer(f"❌ {eliminated_player['name']} вигнано з бункера!")

        voted_users.clear()
        votes.clear()

        if len(players) == 2:
            names = [p["name"] for p in players]
            await message.answer(f"🎉 Переможці: {names[0]} і {names[1]}")
            players.clear()
            global game_started
            game_started = False

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
