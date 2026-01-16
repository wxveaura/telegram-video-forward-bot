import asyncio
import logging
import re
import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "7992125891:AAFuJwtgQHd04PTryqObfsF_IWUYGFoDPlE"
ADMIN_ID = 541518142
DB_PATH = "contest.db"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    language = State()
    region = State()
    phone = State()
    name = State()
    video = State()
    confirm = State()

TEXT = {
    "ru": {
        "start": "👋 Сәлеметсіз бе!  Здравствуйте (Старт /выберите язык)",
        "region": "🌍 Өңірді таңдаңыз/ Выберите регион",
        "phone": "📞 Телефон нөміріңізді енгізіңіз/Введите номер телефона",
        "name": "👤 Аты-жөніңіз/Ф.И.О",
        "video": "Видео жіберіңіз/Отправьте видео",
        "done": "Видео қабылданды\nРақмет/Спасибо",
        "bad_phone": "❌ Неверный номер",
        "not_video": "❌ Нужно отправить видео"
    },
    "kz": {
        "start": "👋 Сәлеметсіз бе!  Здравствуйте (тілді таңдаңыз/выберите язык)",
        "region": "🌍 Өңірді таңдаңыз/ Выберите регион",
        "phone": "📞 Телефон нөміріңізді енгізіңіз/Введите номер телефона",
        "name": "👤 Аты-жөніңіз/Ф.И.О",
        "video": "Видео жіберіңіз/Отправьте видео",
        "done": "Видео қабылданды\nРақмет/Спасибо",
        "bad_phone": "❌ Нөмір қате",
        "not_video": "❌ Видео жіберу керек"
    }
}

REGIONS = [
    "Астана қаласы", "Алматы қаласы", "Шымкент қаласы",
    "Абай облысы", "Ақмола облысы", "Ақтөбе облысы",
    "Алматы облысы", "Атырау облысы", "Шығыс Қазақстан облысы",
    "Жамбыл облысы", "Жетісу облысы", "Батыс Қазақстан облысы",
    "Қарағанды облысы", "Қостанай облысы", "Қызылорда облысы",
    "Маңғыстау облысы", "Павлодар облысы",
    "Солтүстік Қазақстан облысы", "Түркістан облысы", "Ұлытау облысы"
]

REGION_GROUPS = {
    "Астана қаласы": -1003672696864,
    "Алматы қаласы": -1003647472196,
    "Шымкент қаласы": -1003489694186,
    "Абай облысы": -1003525051804,
    "Ақмола облысы": -1003605105665,
    "Ақтөбе облысы": -1003633501309,
    "Алматы облысы": -1003507345886,
    "Атырау облысы": -1003536292459,
    "Шығыс Қазақстан облысы": -1003413906960,
    "Жамбыл облысы": -1003664246516,
    "Жетісу облысы": -1003626218791,
    "Батыс Қазақстан облысы": -1003667833672,
    "Қарағанды облысы": -1003603421624,
    "Қостанай облысы": -1003624411286,
    "Қызылорда облысы": -1003510350437,
    "Маңғыстау облысы": -1003331211493,
    "Павлодар облысы": -1003503882857,
    "Солтүстік Қазақстан облысы": -1003333150416,
    "Түркістан облысы": -1003369623510,
    "Ұлытау облысы": -1003688783725
}

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            language TEXT,
            region TEXT,
            phone TEXT,
            name TEXT,
            video_file_id TEXT
        )
        """)
        await db.commit()

def lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Қазақша", callback_data="lang:kz"),
            InlineKeyboardButton(text="Русский", callback_data="lang:ru")
        ]
    ])

def region_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=r, callback_data=f"region:{r}")]
        for r in REGIONS
    ])

def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Артқа", callback_data="back")]
    ])

def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Дұрыс", callback_data="confirm"),
            InlineKeyboardButton(text="⬅️ Артқа", callback_data="back")
        ]
    ])

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(TEXT["ru"]["start"], reply_markup=lang_kb())
    await state.set_state(Form.language)

@dp.callback_query(F.data.startswith("lang:"))
async def language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split(":")[1]
    await state.update_data(language=lang)
    await callback.message.answer(TEXT[lang]["region"], reply_markup=region_kb())
    await state.set_state(Form.region)
    await callback.answer()

@dp.callback_query(F.data.startswith("region:"))
async def region(callback: CallbackQuery, state: FSMContext):
    region = callback.data.split(":")[1]
    await state.update_data(region=region, confirm_field="region")
    await callback.message.answer(
        f"🏛 {region}\n\nДұрыс па?",
        reply_markup=confirm_kb()
    )
    await state.set_state(Form.confirm)
    await callback.answer()

@dp.message(Form.phone)
async def phone(message: Message, state: FSMContext):
    if not re.fullmatch(r"(\+7|8)\d{10}", message.text.strip()):
        data = await state.get_data()
        await message.answer(TEXT[data["language"]]["bad_phone"])
        return

    phone = message.text.strip()
    await state.update_data(phone=phone, confirm_field="phone")

    await message.answer(
        f"📞 {phone}\n\nДұрыс па?",
        reply_markup=confirm_kb()
    )
    await state.set_state(Form.confirm)

@dp.message(Form.name)
async def name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name, confirm_field="name")

    await message.answer(
        f"👤 {name}\n\nДұрыс па?",
        reply_markup=confirm_kb()
    )
    await state.set_state(Form.confirm)

@dp.callback_query(F.data == "confirm")
async def confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    field = data["confirm_field"]
    lang = data["language"]

    if field == "region":
        await callback.message.answer(TEXT[lang]["phone"], reply_markup=back_kb())
        await state.set_state(Form.phone)

    elif field == "phone":
        await callback.message.answer(TEXT[lang]["name"], reply_markup=back_kb())
        await state.set_state(Form.name)

    elif field == "name":
        await callback.message.answer(TEXT[lang]["video"], reply_markup=back_kb())
        await state.set_state(Form.video)

    await callback.answer()

@dp.message(Form.video)
async def video(message: Message, state: FSMContext):
    data = await state.get_data()

    if not message.video:
        await message.answer(TEXT[data["language"]]["not_video"])
        return

    group_id = REGION_GROUPS.get(data["region"])
    if group_id:
        await bot.send_video(
            group_id,
            message.video.file_id,
            caption=f"{data['region']}\n{data['name']}\n{data['phone']}"
        )

    await message.answer(TEXT[data["language"]]["done"])
    await state.clear()

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current = await state.get_state()
    lang = data.get("language", "ru")

    if current == Form.confirm.state:
        field = data["confirm_field"]

        if field == "region":
            await callback.message.answer(TEXT[lang]["region"], reply_markup=region_kb())
            await state.set_state(Form.region)

        elif field == "phone":
            await callback.message.answer(TEXT[lang]["phone"], reply_markup=back_kb())
            await state.set_state(Form.phone)

        elif field == "name":
            await callback.message.answer(TEXT[lang]["name"], reply_markup=back_kb())
            await state.set_state(Form.name)

    elif current == Form.phone.state:
        await callback.message.answer(TEXT[lang]["region"], reply_markup=region_kb())
        await state.set_state(Form.region)

    elif current == Form.name.state:
        await callback.message.answer(TEXT[lang]["phone"], reply_markup=back_kb())
        await state.set_state(Form.phone)

    elif current == Form.video.state:
        await callback.message.answer(TEXT[lang]["name"], reply_markup=back_kb())
        await state.set_state(Form.name)

    await callback.answer()


async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
