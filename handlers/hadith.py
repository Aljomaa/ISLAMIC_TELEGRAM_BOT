import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import HADITH_API_KEY
from utils.db import add_to_fav
from utils.menu import show_main_menu

BASE_URL = "https://www.hadithapi.com/public/api"

headers = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0"
}

params_base = {
    "apiKey": HADITH_API_KEY,
    "language": "arabic"
}

long_hadith_parts = {}
current_part_index = {}

def register(bot):
    @bot.message_handler(commands=['hadith'])
    def show_hadith_menu_command(msg):
        show_books(bot, msg)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("hadith:"))
    def handle_callback(call):
        bot.answer_callback_query(call.id)
        data = call.data.split(":")
        action = data[1]

        if action == "menu":
            show_books(bot, call.message)

        elif action == "book":
            book_slug = data[2]
            book_name = data[3]
            show_book_options(bot, call.message, book_slug, book_name)

        elif action == "random":
            book_slug = data[2]
            send_random_hadith(bot, call.message, book_slug)

        elif action == "bynumber":
            book_slug = data[2]
            msg = bot.send_message(call.message.chat.id, "📃 أدخل رقم الحديث:")
            bot.register_next_step_handler(msg, lambda m: send_hadith_by_number(bot, m, book_slug))

        elif action == "page":
            book_slug, page, index = data[2], int(data[3]), int(data[4])
            show_hadith_by_index(bot, call.message, book_slug, page, index)

        elif action == "fav":
            user_id = call.from_user.id
            text = call.message.text
            add_to_fav(user_id, text)
            bot.answer_callback_query(call.id, "✅ تم حفظ الحديث في المفضلة")

        elif action == "continue":
            user_id = call.from_user.id
            if user_id in long_hadith_parts and user_id in current_part_index:
                parts = long_hadith_parts[user_id]
                index = current_part_index[user_id] + 1
                if index < len(parts):
                    current_part_index[user_id] = index
                    part_text = parts[index]

                    markup = call.message.reply_markup
                    bot.edit_message_text(
                        part_text,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=markup
                    )
                else:
                    bot.answer_callback_query(call.id, "✅ لا يوجد المزيد من الحديث.")
            else:
                bot.answer_callback_query(call.id, "⚠️ لا يوجد حديث طويل للمتابعة.")

def arabic_book_name(english_name):
    names = {
        "Sahih Bukhari": "صحيح البخاري",
        "Sahih Muslim": "صحيح مسلم",
        "Jami' Al-Tirmidhi": "جامع الترمذي",
        "Sunan Abu Dawood": "سنن أبي داود",
        "Sunan Ibn-e-Majah": "سنن ابن ماجه",
        "Sunan An-Nasa`i": "سنن النسائي",
        "Mishkat Al-Masabih": "مشكاة المصابيح",
        "Musnad Ahmad": "مسند أحمد",
        "Al-Silsila Sahiha": "السلسلة الصحيحة"
    }
    return names.get(english_name, english_name)

def show_books(bot, msg):
    try:
        res = requests.get(f"{BASE_URL}/books", params=params_base, headers=headers)
        books = res.json().get("books", [])
        markup = InlineKeyboardMarkup(row_width=2)
        for book in books:
            name_ar = arabic_book_name(book['bookName'])
            markup.add(
                InlineKeyboardButton(
                    f"📘 {name_ar}",
                    callback_data=f"hadith:book:{book['bookSlug']}:{book['bookName']}"
                )
            )
        markup.add(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu"))
        bot.edit_message_text("📚 اختر كتاب الحديث:", msg.chat.id, msg.message_id, reply_markup=markup)
    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ خطأ: {e}")

def show_book_options(bot, msg, book_slug, book_name):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🎲 حديث عشوائي", callback_data=f"hadith:random:{book_slug}"),
        InlineKeyboardButton("🔢 حديث برقم", callback_data=f"hadith:bynumber:{book_slug}"),
    )
    markup.add(InlineKeyboardButton("⬅️ العودة", callback_data="hadith:menu"))
    bot.edit_message_text("📘 اختر الطريقة:", msg.chat.id, msg.message_id, reply_markup=markup)

def send_random_hadith(bot, msg, book_slug):
    try:
        res = requests.get(f"{BASE_URL}/hadiths", params={**params_base, "book": book_slug, "page": 1}, headers=headers)
        hadiths = res.json().get("hadiths", {}).get("data", [])
        if not hadiths:
            bot.edit_message_text("❌ لا توجد أحاديث في هذا الكتاب.", msg.chat.id, msg.message_id)
            return
        import random
        hadith = random.choice(hadiths)
        send_hadith(bot, msg, hadith, book_slug, page=1, index=hadiths.index(hadith))
    except Exception as e:
        bot.edit_message_text(f"⚠️ خطأ: {e}", msg.chat.id, msg.message_id)

def send_hadith_by_number(bot, msg, book_slug):
    try:
        number = int(msg.text.strip())
        page = (number - 1) // 25 + 1
        index = (number - 1) % 25
        show_hadith_by_index(bot, msg, book_slug, page, index)
    except Exception as e:
        bot.send_message(msg.chat.id, f"⚠️ خطأ: {e}")

def show_hadith_by_index(bot, msg, book_slug, page, index):
    try:
        res = requests.get(f"{BASE_URL}/hadiths", params={**params_base, "book": book_slug, "page": page}, headers=headers)
        data = res.json().get("hadiths", {})
        hadiths = data.get("data", [])
        if index >= len(hadiths):
            bot.send_message(msg.chat.id, "❌ لا يوجد حديث بهذا الرقم.")
            return
        hadith = hadiths[index]
        send_hadith(bot, msg, hadith, book_slug, page, index)
    except Exception as e:
        bot.send_message(msg.chat.id, f"⚠️ خطأ: {e}")

def send_hadith(bot, msg, hadith, book_slug, page, index):
    full_text = f"📌 حديث رقم {hadith['id']}\n\n{hadith.get('hadithArabic', '❌ لا يوجد نص')}"
    user_id = msg.from_user.id if hasattr(msg, 'from_user') else msg.chat.id

    parts = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
    long_hadith_parts[user_id] = parts
    current_part_index[user_id] = 0

    text_to_send = parts[0]
    markup = InlineKeyboardMarkup(row_width=2)

    if len(parts) > 1:
        markup.add(InlineKeyboardButton("📖 متابعة القراءة", callback_data="hadith:continue"))

    if index > 0:
        markup.add(InlineKeyboardButton("⬅️ السابق", callback_data=f"hadith:page:{book_slug}:{page}:{index - 1}"))
    elif page > 1:
        markup.add(InlineKeyboardButton("⬅️ السابق", callback_data=f"hadith:page:{book_slug}:{page - 1}:24"))

    if index < 24:
        markup.add(InlineKeyboardButton("➡️ التالي", callback_data=f"hadith:page:{book_slug}:{page}:{index + 1}"))
    else:
        markup.add(InlineKeyboardButton("➡️ التالي", callback_data=f"hadith:page:{book_slug}:{page + 1}:0"))

    markup.add(
        InlineKeyboardButton("❤️ إضافة للمفضلة", callback_data="hadith:fav"),
        InlineKeyboardButton("📚 الكتب", callback_data="hadith:menu"),
        InlineKeyboardButton("🏠 الرئيسية", callback_data="main_menu")
    )

    try:
        bot.edit_message_text(text_to_send, msg.chat.id, msg.message_id, reply_markup=markup)
    except:
        bot.send_message(msg.chat.id, text_to_send, reply_markup=markup)
