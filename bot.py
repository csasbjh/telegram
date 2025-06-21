from flask import Flask
from threading import Thread
import telebot
from telebot import types
import time
import json
import os

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==== Telegram Bot ====

API_TOKEN = '7985573195:AAEG-o5jU_3A9Umkm1lsPGGefjU-OtchH0A'
ADMIN_ID = 8080902095
DATA_FILE = "users.json"

bot = telebot.TeleBot(API_TOKEN)

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users():
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

users = load_users()

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Бонус дня', 'Запросити друга')
    markup.add('Топ-10', 'Статистика', 'Мій профіль')
    markup.add('Вивести')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    args = message.text.split()

    if user_id not in users:
        users[user_id] = {
            'stars': 0.0,
            'last_bonus': 0,
            'refs_count': 0
        }

    if len(args) > 1:
        ref_id = args[1]
        if ref_id != user_id and ref_id in users:
            users[ref_id]['stars'] += 3
            users[ref_id]['refs_count'] += 1
            bot.send_message(int(ref_id), "🎉 Ви отримали 3 зірки за запрошеного друга!")

    save_users()
    markup = get_main_keyboard()
    bot.send_message(message.chat.id,
                     "Це бот для заробітку зірок.\n"
                     "Реферальна система дає 3 за кожного друга!\n\n"
                     "Використовуй кнопки нижче:",
                     reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'Бонус дня')
def daily_bonus(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        bot.send_message(message.chat.id, "❗ Натисніть /start для початку.")
        return

    now = time.time()
    if now - users[user_id]['last_bonus'] >= 86400:
        users[user_id]['last_bonus'] = now
        users[user_id]['stars'] += 0.1
        bot.send_message(message.chat.id, "✅ Ви отримали 0.1 зірки за сьогодні!")
    else:
        left = int(86400 - (now - users[user_id]['last_bonus']))
        hours = left // 3600
        minutes = (left % 3600) // 60
        bot.send_message(message.chat.id, f"🕒 Зачекайте ще {hours} год {minutes} хв до наступного бонусу.")

    save_users()

@bot.message_handler(func=lambda m: m.text == 'Запросити друга')
def invite(message):
    user_id = str(message.from_user.id)
    link = f"https://t.me/Z1RKA_Official_bot?start={user_id}"
    bot.send_message(message.chat.id, f"🔗 Запроси друга за цим посиланням:\n{link}\n\nЗа друга — 3 зірки!")

@bot.message_handler(func=lambda m: m.text == 'Статистика')
def stats(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        bot.send_message(message.chat.id, "❗ Натисніть /start для початку.")
        return

    stars = users[user_id]['stars']
    refs = users[user_id].get('refs_count', 0)
    bot.send_message(message.chat.id, f"⭐ Ваші зірки: {stars}\n👥 Запрошено друзів: {refs}")

@bot.message_handler(func=lambda m: m.text == 'Мій профіль')
def profile(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        bot.send_message(message.chat.id, "❗ Натисніть /start для початку.")
        return

    stars = users[user_id]['stars']
    refs = users[user_id].get('refs_count', 0)
    bot.send_message(message.chat.id, f"👤 Профіль ID: {user_id}\n⭐ Зірки: {stars}\n👥 Реферали: {refs}")

@bot.message_handler(func=lambda m: m.text == 'Топ-10')
def top_users(message):
    top = sorted(users.items(), key=lambda x: x[1]['stars'], reverse=True)[:10]
    msg = "🏆 Топ-10 користувачів:\n"
    for i, (uid, data) in enumerate(top, start=1):
        msg += f"{i}. ID {uid}: ★ {data['stars']}\n"
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda m: m.text == 'Вивести')
def withdraw(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        bot.send_message(message.chat.id, "❗ Натисніть /start для початку.")
        return

    stars = users[user_id]['stars']
    if stars >= 50.0:
        bot.send_message(message.chat.id, "💬 Введіть свій Telegram username (наприклад: @yourname):")
        bot.register_next_step_handler(message, process_withdraw)
    else:
        bot.send_message(message.chat.id, "❌ Недостатньо зірок. Мінімум 50 потрібно для виводу.")

def process_withdraw(message):
    user_input = message.text.strip()
    user_id = str(message.from_user.id)
    if user_id not in users:
        bot.send_message(message.chat.id, "❗ Натисніть /start для початку.")
        return

    stars = users[user_id]['stars']
    if not user_input.startswith('@'):
        bot.send_message(message.chat.id, "❌ Некоректний формат username. Має починатися з @.")
        bot.register_next_step_handler(message, process_withdraw)
        return

    try:
        bot.send_message(ADMIN_ID, f"💸 ЗАПИТ НА ВИВІД!\nID: {user_id}\nUsername: {user_input}\n⭐ Зірки: {stars}")
        users[user_id]['stars'] = 0.0
        save_users()
        bot.send_message(message.chat.id, "✅ Запит на вивід надіслано адміну. Очікуйте!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка надсилання запиту: {e}")

# ==== Запуск ====
keep_alive()
print("✅ Бот запущено!")
bot.polling(none_stop=True)
