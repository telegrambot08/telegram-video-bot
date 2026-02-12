import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

TOKEN = "8139783286:AAFPqT-N2mF0RHq3UeslaCEZTYLOYROZ6CU"
ADMIN_ID = 7663731929

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# ================= DATABASE =================

async def init_db():
    async with aiosqlite.connect("database.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            lang TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service TEXT,
            package TEXT,
            status TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS promocodes(
            code TEXT PRIMARY KEY,
            discount INTEGER
        )
        """)
        await db.commit()

# ================= TIL TANLASH =================

def lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")]
    ])

@dp.message(CommandStart())
async def start(message: Message):
    banner = "https://i.imgur.com/8Km9tLL.jpg"
    await message.answer_photo(
        banner,
        caption="Tilni tanlang / Выберите язык",
        reply_markup=lang_keyboard()
    )

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    async with aiosqlite.connect("database.db") as db:
        await db.execute("INSERT OR REPLACE INTO users(user_id, lang) VALUES(?,?)",
                         (callback.from_user.id, lang))
        await db.commit()
    await callback.message.answer("✅ Til saqlandi.")
    await show_main_menu(callback.message)

# ================= MENYU =================

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Paket tanlash", callback_data="packages")],
        [InlineKeyboardButton(text="🎁 Promo kod", callback_data="promo")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")]
    ])

async def show_main_menu(message: Message):
    await message.answer("Asosiy menyu:", reply_markup=main_menu())

# ================= PAKETLAR =================

def packages_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🥉 Start - 50 000 so'm", callback_data="pack_start")],
        [InlineKeyboardButton(text="🥈 Business - 100 000 so'm", callback_data="pack_business")],
        [InlineKeyboardButton(text="🥇 Premium - 200 000 so'm", callback_data="pack_premium")]
    ])

@dp.callback_query(F.data == "packages")
async def packages(callback: CallbackQuery):
    await callback.message.answer("Paketni tanlang:", reply_markup=packages_keyboard())

@dp.callback_query(F.data.startswith("pack_"))
async def select_package(callback: CallbackQuery):
    package = callback.data.replace("pack_", "")
    async with aiosqlite.connect("database.db") as db:
        await db.execute("INSERT INTO orders(user_id, service, package, status) VALUES(?,?,?,?)",
                         (callback.from_user.id, "Xizmat", package, "pending"))
        await db.commit()

    pay_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 To'lov qildim", callback_data=f"paid_{callback.from_user.id}")]
    ])

    await callback.message.answer("""
💳 To'lov uchun:

Uzcard: 8600 0000 0000 0000
Humo: 9860 0000 0000 0000

To'lov qilgach pastdagi tugmani bosing.
""", reply_markup=pay_kb)

# ================= PROMO =================

@dp.callback_query(F.data == "promo")
async def promo(callback: CallbackQuery):
    await callback.message.answer("Promo kodni yuboring:")

    dp.message.register(check_promo)

async def check_promo(message: Message):
    code = message.text.strip()
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute("SELECT discount FROM promocodes WHERE code=?",(code,))
        row = await cursor.fetchone()

    if row:
        await message.answer(f"✅ Promo kod qabul qilindi! Chegirma: {row[0]}%")
    else:
        await message.answer("❌ Promo kod noto'g'ri.")

# ================= TO'LOV =================

@dp.callback_query(F.data.startswith("paid_"))
async def paid(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_{user_id}")],
        [InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")]
    ])

    await bot.send_message(ADMIN_ID, f"💰 {user_id} to'lov qildi dedi.", reply_markup=admin_kb)
    await callback.answer("Tekshiruvga yuborildi.")

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    async with aiosqlite.connect("database.db") as db:
        await db.execute("UPDATE orders SET status='paid' WHERE user_id=?",(user_id,))
        await db.commit()
    await bot.send_message(user_id,"✅ Pulingiz qabul qilindi. Buyurtma tasdiqlandi.")
    await callback.answer("Tasdiqlandi.")

@dp.callback_query(F.data.startswith("reject_"))
async def reject(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await bot.send_message(user_id,"❌ To'lov topilmadi.")
    await callback.answer("Rad etildi.")

# ================= STATISTIKA =================

@dp.callback_query(F.data == "stats")
async def stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Faqat admin!")

    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM orders")
        total = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM orders WHERE status='paid'")
        paid = (await cursor.fetchone())[0]

    await callback.message.answer(f"""
📊 Statistika:

Jami buyurtma: {total}
To'langan: {paid}
Kutilmoqda: {total-paid}
""")

# ================= RUN =================

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
