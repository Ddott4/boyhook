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
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@GoCrypto10"
ADMIN_ID = 1580610086
REWARD_LINK = "https://teletype.in/@coinstart/guidestart10"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

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
    [InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="check_sub")]
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
        await message.answer(f"✅ Вы подписаны! Вот ваша ссылка:\n{REWARD_LINK}")
    else:
        await message.answer(
            f"❗ Чтобы получить доступ, подпишитесь на {CHANNEL_USERNAME} и нажмите кнопку ниже:",
            reply_markup=check_sub_button
        )

# ==== ОБРАБОТКА КНОПКИ ====
@dp.callback_query(F.data == "check_sub")
async def handle_check_sub(callback: CallbackQuery):
    user_id = callback.from_user.id

    if await is_subscribed(user_id):
        await callback.message.edit_text(f"✅ Подписка подтверждена!\nВот ваша ссылка: {REWARD_LINK}")
    else:
        await callback.answer("❌ Вы ещё не подписались", show_alert=True)

# ==== /broadcast ====
@dp.message(Command("broadcast"))
async def broadcast(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("❗ Введите сообщение после команды:\nНапример: /broadcast Привет всем!")
        return

    users = get_all_users()
    sent = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, text)
            sent += 1
        except:
            continue

    await message.answer(f"✅ Отправлено {sent} пользователям.")

# ==== WEBHOOK ====
async def on_startup(bot: Bot):
    webhook_url = os.getenv("WEBHOOK_URL")
    await bot.set_webhook(webhook_url)
    print(f"✅ Webhook установлен: {webhook_url}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    await bot.session.close()
    print("❌ Webhook удалён")

async def handle_webhook(request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(bot, update)
    return web.Response()

# ==== ГЛАВНАЯ СТРАНИЦА ====
async def handle_root(request):
    return web.Response(text="✅ Bot is alive!")

# ==== ЗАПУСК ====
init_db()
app = web.Application()
app.router.add_post('/webhook', handle_webhook)
app.router.add_get("/", handle_root)
app.on_startup.append(lambda app: on_startup(bot))
app.on_shutdown.append(lambda app: on_shutdown(bot))

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))



   


