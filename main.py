import telebot
from config import BOT_TOKEN
from handlers import prayers, quran, athkar, favorites, complaints, admin, hadith, settings
from tasks import reminders

import threading
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

ADMIN_ID = 6849903309
bot = telebot.TeleBot(BOT_TOKEN)

# بدء التذكيرات
reminders.start_reminders(bot)

# ✅ عرض القائمة الرئيسية
def show_main_menu(bot, message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🕌 أوقات الصلاة", callback_data="menu:prayer"),
        InlineKeyboardButton("📖 القرآن الكريم", callback_data="menu:quran"),
        InlineKeyboardButton("📿 الأذكار", callback_data="menu:athkar"),
        InlineKeyboardButton("📜 الحديث", callback_data="menu:hadith"),
        InlineKeyboardButton("⭐ المفضلة", callback_data="menu:fav"),
        InlineKeyboardButton("📝 الشكاوى", callback_data="menu:complain"),
        InlineKeyboardButton("⚙️ الإعدادات", callback_data="menu:settings")
    )

    if message.chat.id == ADMIN_ID:
        markup.add(InlineKeyboardButton("🧑‍💼 المشرف", callback_data="menu:admin"))

    bot.edit_message_text("🌙 مرحبًا بك في البوت الإسلامي!\nاختر أحد الخيارات:", message.chat.id, message.message_id, reply_markup=markup)

# ✅ أمر /start
@bot.message_handler(commands=['start'])
def welcome(msg):
    from utils.db import register_user
    register_user(msg.from_user.id)

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🕌 أوقات الصلاة", callback_data="menu:prayer"),
        InlineKeyboardButton("📖 القرآن الكريم", callback_data="menu:quran"),
        InlineKeyboardButton("📿 الأذكار", callback_data="menu:athkar"),
        InlineKeyboardButton("📜 الحديث", callback_data="menu:hadith"),
        InlineKeyboardButton("⭐ المفضلة", callback_data="menu:fav"),
        InlineKeyboardButton("📝 الشكاوى", callback_data="menu:complain"),
        InlineKeyboardButton("⚙️ الإعدادات", callback_data="menu:settings")
    )

    if msg.from_user.id == ADMIN_ID:
        markup.add(InlineKeyboardButton("🧑‍💼 المشرف", callback_data="menu:admin"))

    bot.send_message(msg.chat.id, "🌙 مرحبًا بك في البوت الإسلامي!\nاختر أحد الخيارات:", reply_markup=markup)

# ✅ أزرار القائمة الرئيسية
@bot.callback_query_handler(func=lambda call: call.data.startswith("menu:"))
def handle_main_menu(call):
    bot.answer_callback_query(call.id)
    action = call.data.split(":")[1]

    if action == "prayer":
        from handlers.prayers import show_prayer_times
        show_prayer_times(bot, call.message)

    elif action == "quran":
        from handlers.quran import show_main_quran_menu
        show_main_quran_menu(bot, call.message.chat.id, call.message.message_id)

    elif action == "athkar":
        from handlers.athkar import show_athkar_menu
        show_athkar_menu(bot, call.message)

    elif action == "hadith":
        from handlers.hadith import show_hadith_menu
        show_hadith_menu(bot, call.message)

    elif action == "fav":
        bot.send_message(call.message.chat.id, "/fav")

    elif action == "complain":
        bot.send_message(call.message.chat.id, "/complain")

    elif action == "admin":
        if call.from_user.id == ADMIN_ID:
            bot.send_message(call.message.chat.id, "/admin")
        else:
            bot.send_message(call.message.chat.id, "❌ هذا الخيار مخصص للمشرف فقط.")

    elif action == "settings":
        from handlers.settings import show_settings_menu
        show_settings_menu(bot, call.message.chat.id, call.message.message_id)

# ✅ تسجيل باقي الأوامر
prayers.register(bot)
quran.register(bot)
quran.handle_callbacks(bot)
athkar.register(bot)
favorites.register(bot)
complaints.register(bot)
admin.register(bot)
hadith.register(bot)
settings.register(bot)

# ✅ تشغيل البوت و Flask
def run_bot():
    bot.infinity_polling()

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)
