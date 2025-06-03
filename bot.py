import json
import random
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

TOKEN = "7635553359:AAHKlFZ7h0F6CDuj676jpBhS6v_hLgJseOc"

with open("bunker_cards.json", "r", encoding="utf-8") as file:
    all_cards = json.load(file)

players = {}
revealed_cards = {}

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.id not in players:
        card = random.choice(all_cards)
        while card in players.values():
            card = random.choice(all_cards)
        players[user.id] = card
        revealed_cards[user.id] = {"Професія": True, "Вік": False, "Хобі": False, "Здоров'я": False, "Факт": False}
        context.bot.send_message(chat_id=user.id, text=f"Привіт! Твоя картка:\nПрофесія: {card['Професія']}")
        update.message.reply_text("Ти приєднався до гри. Повна інформація — у приваті.")
    else:
        update.message.reply_text("Ти вже в грі!")

def reveal(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.id not in players:
        update.message.reply_text("Тебе ще нема в грі.")
        return
    args = context.args
    if not args:
        update.message.reply_text("Напиши, яку картку хочеш розкрити (Вік, Хобі, Здоров'я, Факт).")
        return
    field = args[0].capitalize()
    if field not in revealed_cards[user.id]:
        update.message.reply_text("Невірна назва поля.")
        return
    if revealed_cards[user.id][field]:
        update.message.reply_text(f"{field} вже розкрито.")
        return
    revealed_cards[user.id][field] = True
    value = players[user.id][field]
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"{user.first_name} розкрив(ла) {field}: {value}")

def show(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.id not in players:
        update.message.reply_text("Тебе ще нема в грі.")
        return
    card = players[user.id]
    revealed = revealed_cards[user.id]
    text = "Твоя картка:\n"
    for k in card:
        if revealed[k]:
            text += f"{k}: {card[k]}\n"
        else:
            text += f"{k}: ❓\n"
    context.bot.send_message(chat_id=user.id, text=text)

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("reveal", reveal))
    dp.add_handler(CommandHandler("show", show))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
