import asyncio
import os
import sqlite3
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

# ==== НАСТРОЙКИ ====
BOT_TOKEN = os.getenv("8195781148:AAFc9b8CxrX8a9JYEQvN_hUAyjCNflVC5L8")  # Используем переменную окружения
CHANNEL_USERNAME = "@GoCrypto10"
ADMIN_ID = 1580610086

bot = Bot(token="8195781148:AAFc9b8CxrX8a9JYEQvN_hUAyjCNflVC5L8"
, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ==== БАЗА ДАННЫХ SQLite ====
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id: int):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    return [user[0] for user in users]

# ==== КНОПКА ====
check_sub_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="\ud83d\udd04 \u041f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0443", callback_data="check_sub")]
])

# ==== ПРОВЕРКА ПОДПИСКИ ====
async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'creator', 'administrator']
    except:
        return False

# ==== /start ====
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    add_user(user_id)

    if await is_subscribed(user_id):
        await message.answer("\u2705 \u0412\u044b \u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043d\u044b! \u0412\u043e\u0442 \u0432\u0430\u0448\u0430 \u0441\u0441\u044b\u043b\u043a\u0430:\nhttps://teletype.in/@coinstart/bszS77gLhb")
    else:
        await message.answer(
            f"\u2757 \u0427\u0442\u043e\u0431\u044b \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u0434\u043e\u0441\u0442\u0443\u043f, \u043f\u043e\u0434\u043f\u0438\u0448\u0438\u0442\u0435\u0441\u044c \u043d\u0430 {CHANNEL_USERNAME} \u0438 \u043d\u0430\u0436\u043c\u0438\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0443 \u043d\u0438\u0436\u0435:",
            reply_markup=check_sub_button
        )

# ==== ОБРАБОТКА КНОПКИ ====
@dp.callback_query(F.data == "check_sub")
async def handle_check_sub(callback: CallbackQuery):
    user_id = callback.from_user.id

    if await is_subscribed(user_id):
        await callback.message.edit_text("\u2705 \u041f\u043e\u0434\u043f\u0438\u0441\u043a\u0430 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430!\n\u0412\u043e\u0442 \u0432\u0430\u0448\u0430 \u0441\u0441\u044b\u043b\u043a\u0430: https://teletype.in/@coinstart/bszS77gLhb")
    else:
        await callback.answer("\u274c \u0412\u044b \u0435\u0449\u0451 \u043d\u0435 \u043f\u043e\u0434\u043f\u0438\u0441\u0430\u043b\u0438\u0441\u044c", show_alert=True)

# ==== /broadcast ====
@dp.message(Command("broadcast"))
async def broadcast(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("\u2757 \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435 \u043f\u043e\u0441\u043b\u0435 \u043a\u043e\u043c\u0430\u043d\u0434\u044b:\n\u041d\u0430\u043f\u0440\u0438\u043c\u0435\u0440: /broadcast \u041f\u0440\u0438\u0432\u0435\u0442 \u0432\u0441\u0435\u043c!")
        return

    users = get_all_users()
    sent = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, text)
            sent += 1
        except:
            continue

    await message.answer(f"\u2705 \u041e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e {sent} \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f\u043c.")

# ==== WEBHOOK ====
async def on_startup(bot: Bot):
    webhook_url = os.getenv("https://boyhook.onrender.com")
    await bot.set_webhook(webhook_url)
    print(f"\u2705 Webhook установлен: {webhook_url}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    print("\u274c Webhook удалён")

async def handle_webhook(request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(bot, update)
    return web.Response()

# ==== ЗАПУСК ====
init_db()
dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)

app = web.Application()
app.router.add_post("https://boyhook.onrender.com", handle_webhook)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
