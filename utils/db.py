from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["islamic_bot"]

# مجموعات البيانات
user_col = db["users"]
comp_col = db["complaints"]

# ===============================
# ✅ تسجيل المستخدم الجديد
# ===============================
def register_user(user_id):
    if not user_col.find_one({"_id": user_id}):
        user_col.insert_one({"_id": user_id})


# ===============================
# 🕌 الموقع والتوقيت
# ===============================
def set_user_location(user_id, lat, lon, timezone="auto"):
    user_col.update_one(
        {"_id": user_id},
        {"$set": {
            "location.lat": lat,
            "location.lon": lon,
            "timezone": timezone,
            "notifications_enabled": True
        }},
        upsert=True
    )

def get_user_location(user_id):
    user = user_col.find_one({"_id": user_id})
    if user and "location" in user:
        return user["location"].get("lat"), user["location"].get("lon")
    return None, None

def get_user_timezone(user_id):
    user = user_col.find_one({"_id": user_id})
    return user.get("timezone", "auto") if user else "auto"


# ===============================
# 🔔 الإشعارات
# ===============================
def user_notifications_enabled(user_id):
    user = user_col.find_one({"_id": user_id})
    return user.get("notifications_enabled", False) if user else False

def disable_notifications(user_id):
    user_col.update_one({"_id": user_id}, {"$set": {"notifications_enabled": False}})


# ===============================
# ⭐ نظام المفضلة
# ===============================
def add_to_fav(user_id, type_, content):
    user_col.update_one(
        {"_id": user_id},
        {"$push": {"favorites": {"type": type_, "content": content}}},
        upsert=True
    )

def get_user_favs(user_id):
    user = user_col.find_one({"_id": user_id})
    return user.get("favorites", []) if user else []


# ===============================
# 🎧 القارئ المفضل
# ===============================
def get_user_reciter(user_id):
    user = user_col.find_one({"_id": user_id})
    return user.get("reciter") if user else None

def set_user_reciter(user_id, reciter):
    user_col.update_one(
        {"_id": user_id},
        {"$set": {"reciter": reciter}},
        upsert=True
    )


# ===============================
# 🧾 الشكاوى والاقتراحات
# ===============================
def get_complaints():
    return list(comp_col.find({"status": "open"}))

def reply_to_complaint(comp_id, reply_text):
    comp = comp_col.find_one({"_id": comp_id})
    if not comp:
        return False
    user_id = comp["user_id"]
    try:
        from loader import bot
        bot.send_message(user_id, f"📩 رد الإدارة على شكواك:\n\n{reply_text}")
        comp_col.update_one({"_id": comp_id}, {"$set": {"status": "closed"}})
        return True
    except:
        return False


# ===============================
# 📊 الإحصائيات
# ===============================
def get_bot_stats():
    return {
        "total_users": user_col.count_documents({}),
        "total_favorites": user_col.aggregate([
            {"$project": {"count": {"$size": {"$ifNull": ["$favorites", []]}}}},
            {"$group": {"_id": None, "total": {"$sum": "$count"}}}
        ]).next().get("total", 0),
        "total_complaints": comp_col.count_documents({})
    }


# ===============================
# 📢 الرسائل الجماعية
# ===============================
def get_all_users():
    return list(user_col.find({}, {"_id": 1}))

def broadcast_message(bot, message_text):
    for user in get_all_users():
        try:
            bot.send_message(user["_id"], message_text)
        except:
            continue
