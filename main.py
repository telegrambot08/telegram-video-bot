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
    await show_main_menu(callback.message, lang)

# ================= MAIN MENU =================
def main_menu_text(lang):
    if lang == "uz":
        return {
            "reklama": "📢 Reklama",
            "logo": "🎨 Logo Dizayn",
            "telegram_bot": "🤖 Telegram Bot",
            "ishga_qabul": "👥 Ishga Qabul",
            "promokod": "🎁 Promokod",
            "pul_ishlash": "💵 Pul Ishlash",
            "chegirma": "💸 Chegirma",
            "help": "❓ Yordam"
        }
    else:  # Russian
        return {
            "reklama": "📢 Реклама",
            "logo": "🎨 Лого Дизайн",
            "telegram_bot": "🤖 Телеграмм Бот",
            "ishga_qabul": "👥 Прием на работу",
            "promokod": "🎁 Промокод",
            "pul_ishlash": "💵 Заработок",
            "chegirma": "💸 Скидки",
            "help": "❓ Помощь"
        }

def main_menu(lang):
    menu_text = main_menu_text(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=menu_text["reklama"], callback_data="reklama")],
        [InlineKeyboardButton(text=menu_text["logo"], callback_data="logo")],
        [InlineKeyboardButton(text=menu_text["telegram_bot"], callback_data="telegram_bot")],
        [InlineKeyboardButton(text=menu_text["ishga_qabul"], callback_data="ishga_qabul")],
        [InlineKeyboardButton(text=menu_text["promokod"], callback_data="promokod")],
        [InlineKeyboardButton(text=menu_text["pul_ishlash"], callback_data="pul_ishlash")],
        [InlineKeyboardButton(text=menu_text["chegirma"], callback_data="chegirma")],
        [InlineKeyboardButton(text=menu_text["help"], callback_data="help")]
    ])

async def show_main_menu(message: Message, lang):
    await message.answer("Asosiy menyu:", reply_markup=main_menu(lang))

# ================= PROMOKOD =================
@dp.callback_query(F.data == "promokod")
async def promokod(callback: CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    if lang == 'uz':
        await callback.message.answer("Promo kodni yuboring:")
    else:
        await callback.message.answer("Введите промокод:")

@dp.message(F.text)
async def check_promo(message: Message):
    lang = await get_user_lang(message.from_user.id)
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
        if lang == 'uz':
            await message.answer(f"✅ **Promo kod qabul qilindi!** Sizga {amount} so'm ajratildi. Olish uchun @sheraliyevadmin1 profiliga murojaat qiling.")
        else:
            await message.answer(f"✅ **Промокод принят!** Вам начислено {amount} сум. Для получения обратитесь к @sheraliyevadmin1.")
    else:
        if lang == 'uz':
            await message.answer("❌ **Promo kod noto'g'ri.** Iltimos, to'g'ri promo kodni kiriting.")
        else:
            await message.answer("❌ **Неверный промокод.** Пожалуйста, введите правильный промокод.")

# ================= YORDAM =================
@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    if lang == 'uz':
        await callback.message.answer("Yordam uchun @sheraliyevadmin1 bilan bog'laning.")
    else:
        await callback.message.answer("Для помощи свяжитесь с @sheraliyevadmin1.")

# ================= TO'LOVNI QABUL QILISH =================
async def get_user_lang(user_id):
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute("SELECT lang FROM users WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
    return row[0] if row else "uz"  # Default lang is 'uz' (O'zbek)

# ================= MAIN FUNCTION =================
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
