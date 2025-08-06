import asyncio
import os
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import logging
import re

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# Bot tokeni va admin ID (Environment’dan olingan)
TOKEN = os.getenv("TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Bot va Dispatcher obyektlari
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

# Menyular
def create_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚖 Buyurtma berish")],
            [KeyboardButton(text="📞 Aloqa")],
            [KeyboardButton(text="📦 Yetkazib berish")]
        ],
        resize_keyboard=True
    )

def create_direction_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚖 Qo‘qon → Toshkent")],
            [KeyboardButton(text="🚖 Toshkent → Qo‘qon")]
        ],
        resize_keyboard=True
    )

def create_package_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚖 Toshkent → Qo‘qon Yetkazish")],
            [KeyboardButton(text="🚖 Qo‘qon → Toshkent Yetkazish")]
        ],
        resize_keyboard=True
    )

def create_passenger_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 1 kishi"), KeyboardButton(text="👤 2 kishi")],
            [KeyboardButton(text="👤 3 kishi"), KeyboardButton(text="👤 4 kishi")]
        ],
        resize_keyboard=True
    )

def create_cancel_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

# Foydalanuvchi ma'lumotlari
user_data = {}

# /start komandasi
@router.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    user_data[message.from_user.id] = {}
    await message.reply("Assalomu alaykum! Yaypan-Toshkent xizmatiga xush kelibsiz! Qanday yordam beramiz?", reply_markup=create_main_menu())

# Buyurtma berish
@router.message(lambda message: message.text == "🚖 Buyurtma berish")
async def process_order(message: Message):
    user_data.setdefault(message.from_user.id, {})['step'] = 'direction'
    await message.reply("Yo‘nalishingizni tanlang 📍", reply_markup=create_direction_menu())

# Yetkazib berish
@router.message(lambda message: message.text == "📦 Yetkazib berish")
async def process_package(message: Message):
    user_data.setdefault(message.from_user.id, {})['step'] = 'package'
    await message.reply("Yetkazish yo‘nalishingizni tanlang 📦", reply_markup=create_package_menu())

# Yo‘nalish tanlash
@router.message(lambda message: message.text in ["🚖 Qo‘qon → Toshkent", "🚖 Toshkent → Qo‘qon"])
async def set_direction(message: Message):
    user_data.setdefault(message.from_user.id, {})['direction'] = message.text
    user_data[message.from_user.id]['step'] = 'passengers'
    await message.reply("Yo‘lovchilar sonini kiriting 👥", reply_markup=create_passenger_menu())

# Yetkazish yo‘nalishi
@router.message(lambda message: message.text in ["🚖 Toshkent → Qo‘qon Yetkazish", "🚖 Qo‘qon → Toshkent Yetkazish"])
async def set_package_direction(message: Message):
    user_data.setdefault(message.from_user.id, {})['package_direction'] = message.text
    user_data[message.from_user.id]['step'] = 'phone'
    await message.reply("Telefon raqamingizni +998 bilan kiriting (masalan: +998901234567)", reply_markup=create_cancel_menu())

# Yo‘lovchilar soni
@router.message(lambda message: message.text in ["👤 1 kishi", "👤 2 kishi", "👤 3 kishi", "👤 4 kishi"])
async def set_passengers(message: Message):
    if message.from_user.id not in user_data or 'step' not in user_data[message.from_user.id]:
        user_data[message.from_user.id] = {'step': 'passengers'}
    user_data[message.from_user.id]['passengers'] = message.text
    user_data[message.from_user.id]['step'] = 'phone'
    await message.reply("Telefon raqamingizni +998 bilan kiriting (masalan: +998901234567)", reply_markup=create_cancel_menu())

# Bekor qilish
@router.message(lambda message: message.text == "❌ Bekor qilish")
async def cancel_order(message: Message):
    user_data.pop(message.from_user.id, None)
    await message.reply("Buyurtma bekor qilindi. Qayta urinib ko‘ring!", reply_markup=create_main_menu())

# Aloqa
@router.message(lambda message: message.text == "📞 Aloqa")
async def contact_admin(message: Message):
    await message.reply("Admin bilan bog‘lanish: +998905085956 yoki @Voidmekker Telegram’da")

# Telefon raqamini saqlash
@router.message(lambda message: message.text.startswith("+998"))
async def save_details(message: Message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id].get('step') == 'phone':
        if re.match(r"^\+998[0-9]{9}$", message.text):
            user_data[user_id]['phone'] = message.text
            username = message.from_user.username or message.from_user.first_name or str(user_id)
            phone_or_id = user_data[user_id]['phone'] if not message.from_user.username else str(user_id)
            inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=username, url=f"tg://user?id={user_id}")]
            ])
            order_info = (
                f"Yangı buyurtma:\n"
                f"Yo‘nalish: {user_data[user_id].get('direction', user_data[user_id].get('package_direction', 'N/A'))}\n"
                f"Yo‘lovchilar: {user_data[user_id].get('passengers', 'N/A')}\n"
                f"Telefon: {user_data[user_id]['phone']}\n"
                f"Foydalanuvchi: {username} ({phone_or_id if not message.from_user.username else 'ID'})"
            )
            await message.reply("Buyurtmangiz qabul qilindi! ✅", reply_markup=create_main_menu())
            await bot.send_message(ADMIN_ID, order_info, reply_markup=inline_keyboard)
            user_data.pop(user_id, None)
        else:
            await message.reply("Telefon raqam xato! +998XXXXXXXXX formatida kiriting.", reply_markup=create_cancel_menu())
    else:
        await message.reply("Admin bilan bog‘lanish: +998905085956 yoki @Voidmekker Telegram’da", reply_markup=create_main_menu())

# Noto‘g‘ri kiritish
@router.message()
async def handle_invalid(message: Message):
    user_id = message.from_user.id
    if user_id in user_data:
        await message.reply("Noto‘g‘ri buyruq! Iltimos, tugmalardan foydalaning.", reply_markup=create_cancel_menu() if user_data[user_id].get('step') == 'phone' else create_main_menu())
    else:
        await message.reply("Noto‘g‘ri buyruq! Iltimos, tugmalardan foydalaning.", reply_markup=create_main_menu())

# Asosiy funksiya
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())