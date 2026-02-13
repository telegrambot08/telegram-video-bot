import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789

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
    await message.answer("O'zingizga qulay tilni tanlang:", reply_markup=lang_keyboard())

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    async with aiosqlite.connect("database.db") as db:
        await db.execute("INSERT OR REPLACE INTO users(user_id, lang) VALUES(?,?)",
                         (callback.from_user.id, lang))
        await db.commit()
    await callback.message.answer(f"Til tanlandi: {lang}.")
    await show_main_menu(callback.message)

# ================= MAIN MENU =================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Reklama", callback_data="reklama")],
        [InlineKeyboardButton(text="🎨 Logo Dizayn", callback_data="logo")],
        [InlineKeyboardButton(text="🤖 Telegram Bot", callback_data="telegram_bot")],
        [InlineKeyboardButton(text="👥 Ishga Qabul", callback_data="ishga_qabul")],
        [InlineKeyboardButton(text="🎁 Promokod", callback_data="promokod")],
        [InlineKeyboardButton(text="💵 Pul Ishlash", callback_data="pul_ishlash")],
        [InlineKeyboardButton(text="💸 Chegirma", callback_data="chegirma")],
        [InlineKeyboardButton(text="❓ Yordam", callback_data="help")]
    ])

async def show_main_menu(message: Message):
    await message.answer("Asosiy menyu:", reply_markup=main_menu())

# ================= PROMOKOD =================
@dp.callback_query(F.data == "promokod")
async def promokod(callback: CallbackQuery):
    await callback.message.answer("Promo kodni yuboring:")

@dp.message(F.text)
async def check_promo(message: Message):
    code = message.text.strip()
    # Promo kodlarni va ularning pul summalarini belgilang
    promo_codes = {
        'Sheraliyev': 50000,
        'Behruz': 40000,
        'Sevara': 30000,
        'Macho': 20000,
        'Jahongir': 10000,
        'Nobomap': 5000,
    }

    if code in promo_codes:
        amount = promo_codes[code]
        # Promo kod qabul qilinganda foydalanuvchiga info yuboriladi
        await message.answer(f"✅ **Promo kod qabul qilindi!** Sizga {amount} so'm ajratildi. Olish uchun @sheraliyevadmin1 profiliga murojaat qiling.")
    else:
        await message.answer("❌ **Promo kod noto'g'ri.** Iltimos, to'g'ri promo kodni kiriting.")

# ================= YORDAM =================
@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    await callback.message.answer("Yordam uchun @sheraliyevadmin1 bilan bog'laning.")

# ================= REKLAMA =================
@dp.callback_query(F.data == "reklama")
async def reklama(callback: CallbackQuery):
    reklama_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="4 kunlik - 20 000 so'm", callback_data="reklama_4kun")],
        [InlineKeyboardButton(text="1 hafta - 30 000 so'm", callback_data="reklama_1hafta")],
        [InlineKeyboardButton(text="2 hafta - 50 000 so'm", callback_data="reklama_2hafta")],
        [InlineKeyboardButton(text="1 oy - 70 000 so'm", callback_data="reklama_1oy")]
    ])
    await callback.message.answer("Reklama Paketlari:", reply_markup=reklama_menu)

# ================= TO'LOV UCHUN KARTANI TANLASH =================
@dp.callback_query(F.data == "reklama_4kun")
async def reklama_payment(callback: CallbackQuery):
    payment_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Uzcard", callback_data="payment_uzcard")],
        [InlineKeyboardButton(text="💳 Humo", callback_data="payment_humo")],
        [InlineKeyboardButton(text="🔙 Orqaga qaytish", callback_data="back_to_zakazlar")]
    ])
    await callback.message.answer("To'lov uchun kartani tanlang:", reply_markup=payment_kb)

# ================= TO'LOVNI QABUL QILISH =================
@dp.callback_query(F.data.startswith("payment_"))
async def uzcard_payment(callback: CallbackQuery):
    payment_type = callback.data.split("_")[1]
    
    if payment_type == "uzcard":
        card_number = "5614683860045657"
    elif payment_type == "humo":
        card_number = "9860167834405026"

    payment_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📍 {payment_type.upper()}: {card_number}", callback_data=f"paid_{payment_type}")],
        [InlineKeyboardButton(text="💳 To'lov qildim", callback_data=f"paid_{payment_type}")],
        [InlineKeyboardButton(text="🔙 Orqaga qaytish", callback_data="back_to_reklama")]
    ])
    await callback.message.answer(f"Ilmamos, kartangizni tanlang va to'lovni amalga oshiring:", reply_markup=payment_kb)

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

# ================= MAIN FUNCTION =================
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
