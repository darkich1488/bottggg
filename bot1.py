import random
import string
import os

from flask import Flask
from threading import Thread

import telebot
from telebot import types


# --- КОНФІГУРАЦІЯ З RAILWAY VARIABLES ---
API_TOKEN = os.getenv("API_TOKEN")

if not API_TOKEN:
    raise ValueError("API_TOKEN не знайдено в Railway Variables")

if ":" not in API_TOKEN:
    raise ValueError("API_TOKEN некоректний: у токені немає двокрапки")

ADMIN_ID = int(os.getenv("ADMIN_ID", "925896498"))
MARKETING_ID = int(os.getenv("MARKETING_ID", "925896498"))
SECOND_ADMIN_ID = int(os.getenv("SECOND_ADMIN_ID", "8619205109"))

CHANNEL_ID = os.getenv("CHANNEL_ID", "@heaphestwarp")
REVIEWS_LINK = os.getenv("REVIEWS_LINK", "https://t.me/repheaphest")
PAYMENT_REQUISITES = os.getenv(
    "PAYMENT_REQUISITES",
    "Картка: 4874070053789234 (Моно) Денис Ф."
)

ADMINS = [ADMIN_ID, MARKETING_ID, SECOND_ADMIN_ID]

bot = telebot.TeleBot(API_TOKEN)
app = Flask('')


# База даних та стани
user_db = set()
marketing_state = {}


# --- ВЕБ-СЕРВЕР ДЛЯ ПІДТРИМКИ ЖИТТЄЗДАТНОСТІ ---
@app.route('/')
def home():
    return "Bot is alive!"


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
        allowed = ['member', 'administrator', 'creator']
        return status_channel in allowed
    except Exception:
        return False


# --- КЛАВІАТУРИ ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("⭐ Купити зірки", "💎 Купити Premium")
    markup.add("📱 Вірт. номери", "💬 Відгуки")
    markup.add("🆘 Тех. Підтримка")
    return markup


def virt_numbers_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🇺🇸 США — 80₴", callback_data="buy|Virt|USA|80₴"),
        types.InlineKeyboardButton("🇰🇪 Кенія — 80₴", callback_data="buy|Virt|Kenya|80₴"),
        types.InlineKeyboardButton("🇨🇦 Канада — 80₴", callback_data="buy|Virt|Canada|80₴"),
        types.InlineKeyboardButton("🇰🇿 Казахстан — 120₴", callback_data="buy|Virt|Kazakhstan|120₴"),
        types.InlineKeyboardButton("🇺🇦 Україна — 120₴", callback_data="buy|Virt|Ukraine|120₴"),
        types.InlineKeyboardButton("🇷🇺 Росія — 120₴", callback_data="buy|Virt|Russia|120₴")
    )
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


# --- ОБРОБНИКИ КОМАНД ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type != 'private':
        return

    user_db.add(message.from_user.id)

    if check_subscribe(message.from_user.id):
        welcome_text = f"<b>Привіт, {message.from_user.first_name}!</b> 👋\n✨ Вітаємо в <b>H&K SALE BOT</b>!"
        bot.send_message(
            message.chat.id,
            welcome_text,
            parse_mode='HTML',
            reply_markup=main_menu()
        )
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "📢 Підписатися на канал",
                url=f"https://t.me/{CHANNEL_ID[1:]}"
            )
        )
        markup.add(types.InlineKeyboardButton("Я підписався ✅", callback_data="check"))
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Доступ обмежений!</b>\nДля використання бота підпишіться на наш канал:",
            parse_mode='HTML',
            reply_markup=markup
        )


@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id in ADMINS:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Створити розсилку", callback_data="mkt_start"))
        bot.send_message(
            message.chat.id,
            "🛠 <b>Панель управління</b>",
            parse_mode='HTML',
            reply_markup=markup
        )


# --- CALLBACKS ---
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    if call.data == "check":
        if check_subscribe(call.from_user.id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ Доступ відкрито!", reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, "❌ Ви все ще не підписані!", show_alert=True)

    elif call.data == "mkt_start":
        if call.from_user.id not in ADMINS:
            bot.answer_callback_query(call.id, "Немає доступу", show_alert=True)
            return

        marketing_state[call.from_user.id] = "waiting_promo"
        bot.edit_message_text(
            "📸 <b>Надішліть фото з описом</b> для розсилки:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )

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

        bot.edit_message_text(
            f"💎 Оберіть термін ({p_type}):",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

    elif call.data.startswith("buy|"):
        _, category, name, price = call.data.split("|")
        order_code = generate_order_code()

        pay_text = (
            f"<b>💳 Оформлення: {category} {name}</b>\n\n"
            f"💵 <b>До сплати: {price}</b>\n"
            f"📝 Коментар: <code>{order_code}</code>\n\n"
            f"<b>Реквізити:</b>\n{PAYMENT_REQUISITES}\n\n"
            "❗ <i>Надішліть скріншот чеку сюди в бот.</i>"
        )

        msg = bot.send_message(call.message.chat.id, pay_text, parse_mode='HTML')
        bot.register_next_step_handler(msg, process_payment_proof, f"{category} {name}", price, order_code)

    elif "adm_" in call.data:
        if call.from_user.id not in ADMINS:
            bot.answer_callback_query(call.id, "Немає доступу", show_alert=True)
            return

        parts = call.data.split("_")
        action, target_id = parts[1], int(parts[2])

        if action == "confirm":
            bot.send_message(
                target_id,
                "🌟 <b>Оплата підтверджена!</b>\nВаше замовлення виконується.",
                parse_mode='HTML'
            )
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=call.message.caption + "\n\n✅ <b>ПІДТВЕРДЖЕНО</b>",
                reply_markup=None
            )

        elif action == "decline":
            bot.send_message(
                target_id,
                "❌ <b>Оплата відхилена.</b>\nЗв'яжіться з підтримкою.",
                parse_mode='HTML'
            )
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=call.message.caption + "\n\n❌ <b>ВІДХИЛЕНО</b>",
                reply_markup=None
            )


# --- ПРИЙОМ ОПЛАТИ ТА РОЗСИЛКА ---
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    if marketing_state.get(message.from_user.id) == "waiting_promo":
        if message.from_user.id not in ADMINS:
            return

        marketing_state.pop(message.from_user.id)

        count = 0
        for user_id in list(user_db):
            try:
                bot.send_photo(
                    user_id,
                    message.photo[-1].file_id,
                    caption=message.caption,
                    parse_mode='HTML'
                )
                count += 1
            except Exception:
                continue

        bot.send_message(message.chat.id, f"✅ Розсилка завершена! Отримали: {count} юзерів.")


def process_payment_proof(message, item_name, price, order_code):
    if not message.photo:
        msg = bot.reply_to(message, "❌ Надішліть саме <b>фото чеку</b>.", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_payment_proof, item_name, price, order_code)
        return

    bot.send_message(
        message.chat.id,
        "✅ <b>Заявка надіслана!</b> Очікуйте підтвердження.",
        parse_mode='HTML'
    )

    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(
        types.InlineKeyboardButton("✅ Прийняти", callback_data=f"adm_confirm_{message.chat.id}"),
        types.InlineKeyboardButton("❌ Відхилити", callback_data=f"adm_decline_{message.chat.id}")
    )

    username = f"@{message.from_user.username}" if message.from_user.username else "немає username"

    caption = (
        f"🔔 <b>ЗАМОВЛЕННЯ</b>\n"
        f"👤 {username}\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"📦 Товар: {item_name}\n"
        f"💰 Сума: {price}\n"
        f"🔑 Код: <code>{order_code}</code>"
    )

    for admin_id in ADMINS:
        try:
            bot.send_photo(
                admin_id,
                message.photo[-1].file_id,
                caption=caption,
                parse_mode='HTML',
                reply_markup=admin_markup
            )
        except Exception:
            pass


# --- ТЕКСТОВІ КОМАНДИ ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_db.add(message.from_user.id)

    if message.text == "⭐ Купити зірки":
        bot.send_message(
            message.chat.id,
            "✨ <b>Оберіть пакет Stars:</b>",
            parse_mode='HTML',
            reply_markup=buy_stars_menu()
        )

    elif message.text == "💎 Купити Premium":
        bot.send_message(
            message.chat.id,
            "💎 <b>Оберіть тип активації:</b>",
            parse_mode='HTML',
            reply_markup=premium_choice_menu()
        )

    elif message.text == "📱 Вірт. номери":
        bot.send_message(
            message.chat.id,
            "📱 <b>Оберіть країну номера:</b>",
            parse_mode='HTML',
            reply_markup=virt_numbers_menu()
        )

    elif message.text == "💬 Відгуки":
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("Переглянути 📝", url=REVIEWS_LINK)
        )
        bot.send_message(message.chat.id, "Відгуки наших клієнтів:", reply_markup=markup)

    elif message.text == "🆘 Тех. Підтримка":
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("Менеджер 📩", url="https://t.me/garant_mango")
        )
        bot.send_message(message.chat.id, "Маєте запитання? Пишіть нам!", reply_markup=markup)


if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling(skip_pending=True)
