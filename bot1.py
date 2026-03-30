import telebot
from telebot import types
import random
import string
import os
from flask import Flask
from threading import Thread

# --- КОНФІГУРАЦІЯ ---
API_TOKEN = '8745362560:AAF2rJV_zyoKAkYVlj8TuXqPipP_0ArkTrQ'
ADMIN_ID = 925896498
MARKETING_ID = 8410539247  # ID Маркетолога
CHANNEL_ID = '@mango_tg_shop'
CHAT_ID = '@mango_markt'
REVIEWS_LINK = 'https://t.me/rewiews_mango'
PAYMENT_REQUISITES = "Картка: 4149497510707369 (Приват) Шклярчук Й."

bot = telebot.TeleBot(API_TOKEN)
app = Flask('')

# База користувачів (у пам'яті)
user_db = set() 
user_feedback_state = {}
marketing_state = {}

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
@app.route('/')
def home():
    return "I'm alive"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- ДОПОМІЖНІ ФУНКЦІЇ ---
def generate_order_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def check_subscribe(user_id):
    try:
        status_channel = bot.get_chat_member(CHANNEL_ID, user_id).status
        status_chat = bot.get_chat_member(CHAT_ID, user_id).status
        allowed = ['member', 'administrator', 'creator']
        return status_channel in allowed and status_chat in allowed
    except Exception as e:
        print(f"Помилка перевірки: {e}")
        return False

# --- КЛАВІАТУРИ ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("⭐ Купити зірки", "💎 Купити Premium")
    markup.add("💬 Відгуки", "🆘 Тех. Підтримка")
    return markup

def buy_stars_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("50 ⭐️ — 65₴", callback_data="buy|Stars|50|65₴"),
        types.InlineKeyboardButton("100 ⭐️ — 125₴", callback_data="buy|Stars|100|125₴"),
        types.InlineKeyboardButton("250 ⭐️ — 290₴", callback_data="buy|Stars|250|290₴"),
        types.InlineKeyboardButton("500 ⭐️ — 550₴", callback_data="buy|Stars|500|550₴")
    )
    return markup

def premium_choice_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔑 Вхід в аккаунт (Дешевше)", callback_data="prem_type_Login"),
        types.InlineKeyboardButton("🎁 Подарунком (Без входу)", callback_data="prem_type_Gift")
    )
    return markup

# --- ОБРОБНИКИ ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type != 'private': return
    user_db.add(message.from_user.id)
    
    if check_subscribe(message.from_user.id):
        welcome_text = f"<b>Привіт, {message.from_user.first_name}!</b> 👋\n\n✨ Вітаємо в <b>Mango Shop</b>!"
        bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=main_menu())
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Канал", url=f"https://t.me/{CHANNEL_ID[1:]}"))
        markup.add(types.InlineKeyboardButton("💬 Чат", url=f"https://t.me/{CHAT_ID[1:]}"))
        markup.add(types.InlineKeyboardButton("Я підписався ✅", callback_data="check"))
        bot.send_message(message.chat.id, "⚠️ <b>Доступ обмежений!</b>\nБудь ласка, підпишіться:", 
                         parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    if call.data == "check":
        if check_subscribe(call.from_user.id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ Доступ відкрито!", reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, "❌ Ви все ще не підписані!", show_alert=True)
    
    elif call.data.startswith("prem_type_"):
        p_type = call.data.split("_")[2]
        bot.edit_message_text(f"💎 Оберіть термін ({p_type}):", call.message.chat.id, call.message.message_id, reply_markup=buy_stars_menu()) # Спростив для тесту

    elif call.data.startswith("buy|"):
        _, category, name, price = call.data.split("|")
        order_code = generate_order_code()
        pay_text = f"<b>💳 Оплата: {category} {name}</b>\nСплатіть {price} та надішліть скрін.\nКод: <code>{order_code}</code>"
        msg = bot.edit_message_text(pay_text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
        bot.register_next_step_handler(msg, process_payment_proof, f"{category} {name}", price, order_code)

def process_payment_proof(message, item_name, price, order_code):
    if not message.photo:
        msg = bot.reply_to(message, "❌ Надішліть фото чеку.")
        bot.register_next_step_handler(msg, process_payment_proof, item_name, price, order_code)
        return
    
    bot.send_message(message.chat.id, "✅ Заявка надіслана!")
    caption = f"🔔 НОВЕ ЗАМОВЛЕННЯ\nТовар: {item_name}\nСума: {price}\nКод: {order_code}"
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "⭐ Купити зірки":
        bot.send_message(message.chat.id, "✨ Оберіть пакет:", reply_markup=buy_stars_menu())
    elif message.text == "💎 Купити Premium":
        bot.send_message(message.chat.id, "💎 Оберіть тип:", reply_markup=premium_choice_menu())

# --- ЗАПУСК ---
if __name__ == '__main__':
    keep_alive() # Запускаємо Flask в фоні
    print("Сервер та Бот запускаються...")
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Помилка: {e}")
