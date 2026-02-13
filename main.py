import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

TOKEN = "8139783286:AAFA_G7JcvWaBMj7ZIUwISoSbRwnv8jZ8Rk"
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

# ================= Oʻzingizga qulay tilni tanlang =================
def lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbek Tili", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Rus Tili", callback_data="lang_ru")]
    ])

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Iltimos, o'zingizga qulay tilni tanlang:", reply_markup=lang_keyboard())

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    async with aiosqlite.connect("database.db") as db:
        await db.execute("INSERT OR REPLACE INTO users(user_id, lang) VALUES(?,?)",
                         (callback.from_user.id, lang))
        await db.commit()
    await callback.message.answer(f"Til saqlandi: {lang.capitalize()}")
    await show_main_menu(callback.message)

# ================= MENYU =================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔹 **Zakazlar Menyusi**", callback_data="zakazlar")],
        [InlineKeyboardButton(text="🔸 **Promokod Kiritish**", callback_data="promokod")],
        [InlineKeyboardButton(text="🔹 **Pul Ishlash Bo'limi**", callback_data="pul_ishlash")],
        [InlineKeyboardButton(text="❓ **Yordam**", callback_data="help")]
    ])

async def show_main_menu(message: Message):
    await message.answer("Asosiy menyu:", reply_markup=main_menu())

# ================= ZAKAZLAR MENYUSI =================
@dp.callback_query(F.data == "zakazlar")
async def zakazlar(callback: CallbackQuery):
    zakaz_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 **Reklama Paketlari**", callback_data="reklama")],
        [InlineKeyboardButton(text="🎨 **Logo Dizayn Xizmatlari**", callback_data="logo")],
        [InlineKeyboardButton(text="🤖 **Telegram Bot Xizmatlari**", callback_data="telegram_bot")]
    ])
    await callback.message.answer("Zakazlar Menyusi:", reply_markup=zakaz_menu)

@dp.callback_query(F.data == "reklama")
async def reklama(callback: CallbackQuery):
    reklama_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="4 kunlik reklama - 20 000 so'm", callback_data="reklama_4kun")],
        [InlineKeyboardButton(text="1 hafta reklama - 30 000 so'm", callback_data="reklama_1hafta")],
        [InlineKeyboardButton(text="2 hafta reklama - 50 000 so'm", callback_data="reklama_2hafta")],
        [InlineKeyboardButton(text="1 oy reklama - 70 000 so'm", callback_data="reklama_1oy")]
    ])
    await callback.message.answer("Reklama Paketlari:", reply_markup=reklama_menu)

@dp.callback_query(F.data.startswith("reklama_"))
async def reklama_payment(callback: CallbackQuery):
    payment_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 To'lovni amalga oshirdim", callback_data=f"paid_{callback.data}")],
        [InlineKeyboardButton(text="🔙 Orqaga qaytish", callback_data="back_to_zakazlar")]
    ])
    await callback.message.answer("To'lov uchun kartani tanlang:", reply_markup=payment_kb)

@dp.callback_query(F.data.startswith("paid_"))
async def paid(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ **Tasdiqlash**", callback_data=f"confirm_{user_id}")],
        [InlineKeyboardButton(text="❌ **Rad etish**", callback_data=f"reject_{user_id}")]
    ])
    await bot.send_message(ADMIN_ID, f"💰 Foydalanuvchi {user_id} to'lovni amalga oshirdi.", reply_markup=admin_kb)
    await callback.answer("To'lovni tasdiqlash uchun adminga yuborildi.")

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    async with aiosqlite.connect("database.db") as db:
        await db.execute("UPDATE orders SET status='paid' WHERE user_id=?", (user_id,))
        await db.commit()
    await bot.send_message(user_id, "✅ **To'lov qabul qilindi.**")
    await callback.answer("To'lov tasdiqlandi.")

@dp.callback_query(F.data.startswith("reject_"))
async def reject(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await bot.send_message(user_id, "❌ **To'lov topilmadi.**")
    await callback.answer("To'lov rad etildi.")

# ================= PROMOKOD =================
@dp.callback_query(F.data == "promokod")
async def promokod(callback: CallbackQuery):
    await callback.message.answer("Iltimos, promo kodni yuboring:")

    dp.message.register(check_promo)

async def check_promo(message: Message):
    code = message.text.strip()
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute("SELECT discount FROM promocodes WHERE code=?", (code,))
        row = await cursor.fetchone()

    if row:
        await message.answer(f"✅ **Promo kod qabul qilindi! Chegirma: {row[0]}%**")
    else:
        await message.answer("❌ **Promo kod noto'g'ri.**")

# ================= YORDAM =================
@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    await callback.message.answer("Yordam uchun @sheraliyevadmin1 bilan bog'laning.")

# ================= TO'LOV KARTALARI =================
@dp.callback_query(F.data.startswith("paid_"))
async def display_payment_methods(callback: CallbackQuery):
    payment_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Uzcard: 5614683860045657", callback_data="uzcard_payment")],
        [InlineKeyboardButton(text="Humo: 9860167834405026", callback_data="humo_payment")],
        [InlineKeyboardButton(text="💳 To'lovni amalga oshirdim", callback_data=f"paid_{callback.data}")],
        [InlineKeyboardButton(text="🔙 Orqaga qaytish", callback_data="back_to_zakazlar")]
    ])
    await callback.message.answer("Iltimos, kartangizni tanlang va to'lovni amalga oshiring:", reply_markup=payment_kb)

# ================= RUN =================
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
