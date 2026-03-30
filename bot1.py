import telebot
from telebot import types
import random
import string

# --- КОНФІГУРАЦІЯ ---
API_TOKEN = '8745362560:AAF2rJV_zyoKAkYVlj8TuXqPipP_0ArkTrQ'
ADMIN_ID = 925896498
MARKETING_ID = 8410539247  # ID Маркетолога
CHANNEL_ID = '@mango_tg_shop'
CHAT_ID = '@mango_markt'
REVIEWS_LINK = 'https://t.me/rewiews_mango'
PAYMENT_REQUISITES = "Картка: 4149497510707369 (Приват) Шклярчук Й."

bot = telebot.TeleBot(API_TOKEN)

# База користувачів (у пам'яті)
user_db = set() 

# Словники для станів
user_feedback_state = {}
marketing_state = {}

# --- ДОПОМІЖНІ ФУНКЦІЇ ---
def generate_order_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def check_subscribe(user_id):
    try:
        # Перевірка підписки на канал та чат
        status_channel = bot.get_chat_member(CHANNEL_ID, user_id).status
        status_chat = bot.get_chat_member(CHAT_ID, user_id).status
        allowed = ['member', 'administrator', 'creator']
        return status_channel in allowed and status_chat in allowed
    except Exception:
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

def marketing_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Створити розсилку", callback_data="mkt_start"))
    return markup

# --- ОБРОБНИКИ ---

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type != 'private': return
    
    user_db.add(message.from_user.id)
    
    if check_subscribe(message.from_user.id):
        welcome_text = (
            f"<b>Привіт, {message.from_user.first_name}!</b> 👋\n\n"
            "✨ Вітаємо в <b>Mango Shop</b>!\n"
            "Тут ти можеш швидко та безпечно придбати Telegram Stars та Premium."
        )
        bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=main_menu())
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Канал", url=f"https://t.me/{CHANNEL_ID[1:]}"))
        markup.add(types.InlineKeyboardButton("💬 Чат", url=f"https://t.me/{CHAT_ID[1:]}"))
        markup.add(types.InlineKeyboardButton("Я підписався ✅", callback_data="check"))
        bot.send_message(message.chat.id, "⚠️ <b>Доступ обмежений!</b>\nБудь ласка, підпишіться на наші ресурси:", 
                         parse_mode='HTML', reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == MARKETING_ID or message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🛠 <b>Панель управління</b>\nТут ви можете зробити розсилку фото + текст.", 
                         parse_mode='HTML', reply_markup=marketing_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    # Маркетинг
    if call.data == "mkt_start":
        if call.from_user.id == MARKETING_ID or call.from_user.id == ADMIN_ID:
            marketing_state[call.from_user.id] = "waiting_promo"
            bot.edit_message_text("📸 <b>Надішліть фото з описом</b>, яке потрібно розіслати всім користувачам:", 
                                 call.message.chat.id, call.message.message_id, parse_mode='HTML')

    # Перевірка підписки
    elif call.data == "check":
        if check_subscribe(call.from_user.id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ Доступ відкрито! Головне меню:", reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, "❌ Ви все ще не підписані!", show_alert=True)

    # Вибір типу Premium
    elif call.data.startswith("prem_type_"):
        p_type = call.data.split("_")[2]
        markup = types.InlineKeyboardMarkup(row_width=1)
        if p_type == "Login":
            markup.add(
                types.InlineKeyboardButton("12 міс. — 980₴", callback_data="buy|Prem(Login)|12міс|980₴"),
                types.InlineKeyboardButton("1 міс. — 140₴", callback_data="buy|Prem(Login)|1міс|140₴")
            )
        else:
            markup.add(
                types.InlineKeyboardButton("12 міс. — 1400₴", callback_data="buy|Prem(Gift)|12міс|1400₴"),
                types.InlineKeyboardButton("3 міс. — 550₴", callback_data="buy|Prem(Gift)|3міс|550₴")
            )
        bot.edit_message_text(f"💎 Оберіть термін ({p_type}):", call.message.chat.id, call.message.message_id, reply_markup=markup)

    # Купівля (оформлення)
    elif call.data.startswith("buy|"):
        _, category, name, price = call.data.split("|")
        item_full_name = f"{category} {name}"
        order_code = generate_order_code()
        pay_text = (f"<b>💳 Оформлення: {item_full_name}</b>\n\n💵 <b>До сплати: {price}</b>\n"
                    f"📝 Коментар: <code>{order_code}</code>\n\n<b>Реквізити:</b>\n{PAYMENT_REQUISITES}\n\n"
                    "❗ <i>Надішліть скріншот чеку сюди в бот.</i>")
        msg = bot.edit_message_text(pay_text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
        bot.register_next_step_handler(msg, process_payment_proof, item_full_name, price, order_code)

    # Адмін-дії
    elif call.data.startswith("adm_"):
        data = call.data.split("_")
        action = data[1]
        target_user_id = data[2]
        
        if action == "confirm":
            bot.send_message(target_user_id, "🌟 <b>Оплата підтверджена!</b>\nВаше замовлення вже виконується менеджером.", parse_mode='HTML')
            done_markup = types.InlineKeyboardMarkup()
            done_markup.add(types.InlineKeyboardButton("✅ ВИКОНАНО", callback_data=f"adm_done_{target_user_id}"))
            bot.edit_message_caption(call.message.caption + "\n\n✅ Оплата прийнята. Чекаємо виконання.", call.message.chat.id, call.message.message_id, reply_markup=done_markup)
            
        elif action == "done":
            feedback_markup = types.InlineKeyboardMarkup()
            feedback_markup.add(types.InlineKeyboardButton("✍️ Залишити відгук", callback_data="give_feedback"))
            feedback_markup.add(types.InlineKeyboardButton("❌ Пропустити", callback_data="skip_feedback"))
            bot.send_message(target_user_id, "🎁 <b>Ваше замовлення виконано!</b>\nБудемо вдячні за відгук.", parse_mode='HTML', reply_markup=feedback_markup)
            bot.edit_message_caption(call.message.caption + "\n\n📦 ВИКОНАНО", call.message.chat.id, call.message.message_id, reply_markup=None)
            
        elif action == "decline":
            bot.send_message(target_user_id, "❌ <b>Оплата відхилена.</b>\nЗв'яжіться з підтримкою: @garant_mango", parse_mode='HTML')
            bot.edit_message_caption(call.message.caption + "\n\n❌ ВІДХИЛЕНО", call.message.chat.id, call.message.message_id, reply_markup=None)

    elif call.data == "give_feedback":
        user_feedback_state[call.from_user.id] = True
        bot.edit_message_text("Ваше замовлення виконане ✅\n\nЗалиште відгук (фото + текст) і тегніть @managerMANGO. Ми перешлемо його адміну!", call.message.chat.id, call.message.message_id)

    elif call.data == "skip_feedback":
        bot.edit_message_text("Дякуємо за покупку! Гарного дня!", call.message.chat.id, call.message.message_id)

# --- ОБРОБКА МАРКЕТИНГУ ---
@bot.message_handler(content_types=['photo'], func=lambda m: marketing_state.get(m.from_user.id) == "waiting_promo")
def handle_marketing_promo(message):
    marketing_state.pop(message.from_user.id, None)
    
    photo_id = message.photo[-1].file_id
    caption = message.caption if message.caption else ""
    
    count = 0
    admins = [ADMIN_ID, MARKETING_ID]
    
    for user_id in user_db:
        try:
            bot.send_photo(user_id, photo_id, caption=caption, parse_mode='HTML')
            count += 1
        except Exception:
            continue
                
    bot.send_message(message.chat.id, f"✅ Розсилка завершена!\nОтримали: {count} користувачів.")

# --- ПРИЙОМ ОПЛАТИ ---
def process_payment_proof(message, item_name, price, order_code):
    if not message.photo:
        msg = bot.reply_to(message, "❌ Надішліть саме <b>фото/скріншот</b> чеку.")
        bot.register_next_step_handler(msg, process_payment_proof, item_name, price, order_code)
        return

    bot.send_message(message.chat.id, "✅ <b>Заявка надіслана!</b> Очікуйте підтвердження.", parse_mode='HTML')
    
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(
        types.InlineKeyboardButton("✅ Оплата прийшла", callback_data=f"adm_confirm_{message.chat.id}"),
        types.InlineKeyboardButton("❌ Відхилити", callback_data=f"adm_decline_{message.chat.id}")
    )
    
    username = f"@{message.from_user.username}" if message.from_user.username else "Немає"
    caption = (f"🔔 <b>НОВЕ ЗАМОВЛЕННЯ</b>\n\n👤 <b>Покупець:</b> {username}\n🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
               f"📦 <b>Товар:</b> {item_name}\n💰 <b>Сума:</b> {price}\n🔑 <b>Код:</b> <code>{order_code}</code>")
    
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, parse_mode='HTML', reply_markup=admin_markup)

# --- ВІДГУКИ ---
@bot.message_handler(func=lambda message: user_feedback_state.get(message.from_user.id) == True, content_types=['text', 'photo', 'video'])
def handle_feedback_submission(message):
    user_feedback_state.pop(message.from_user.id, None)
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(ADMIN_ID, f"☝️ <b>Отримано новий відгук від користувача {message.from_user.id}!</b>", parse_mode='HTML')
    bot.send_message(message.chat.id, "✅ <b>Ваш відгук надіслано!</b> Дякуємо за довіру.", parse_mode='HTML')

# --- ТЕКСТОВІ КОМАНДИ ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.chat.type != 'private': return
    
    user_db.add(message.from_user.id)

    if not check_subscribe(message.from_user.id):
        start(message)
        return

    if message.text == "⭐ Купити зірки":
        bot.send_message(message.chat.id, "✨ <b>Оберіть пакет Stars:</b>", parse_mode='HTML', reply_markup=buy_stars_menu())
    elif message.text == "💎 Купити Premium":
        bot.send_message(message.chat.id, "💎 <b>Оберіть спосіб активації:</b>", parse_mode='HTML', reply_markup=premium_choice_menu())
    elif message.text == "💬 Відгуки":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Читати відгуки 📝", url=REVIEWS_LINK))
        bot.send_message(message.chat.id, "Наші клієнти кажуть:", reply_markup=markup)
    elif message.text == "🆘 Тех. Підтримка":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Написати менеджеру 📩", url="https://t.me/garant_mango"))
        bot.send_message(message.chat.id, "Виникли питання? Ми допоможемо!", reply_markup=markup)

if __name__ == '__main__':
    print("Бот запущений...")
    bot.infinity_polling()

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == '__main__':
    print("Запуск веб-сервера...")
    keep_alive()  # Запускаем сервер в отдельном потоке
    print("Бот запущен...")
    bot.infinity_polling()
