import asyncio
import logging
from aiogram import Dispatcher, F
from aiogram.client.bot import Bot, DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    PreCheckoutQuery,
    LabeledPrice,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)

# Токен бота
BOT_TOKEN = "ВАШ_ТОКЕН"
ADMIN_ID = 1763797493  # ID администратора

# База заказов
user_data = {}

# Создаем объект бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


# --- Команда /start (Главное меню) ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """
    Главное меню с выбором заказа.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Заказать мед фацелиевый", callback_data="order_honey")],
            [InlineKeyboardButton(text="Заказать мед майский", callback_data="order_honey2")],
            [InlineKeyboardButton(text="Заказать мед подсолнечный", callback_data="order_honey3")],
            [InlineKeyboardButton(text="Связаться с поддержкой", callback_data="contact_support")]
        ]
    )

    await message.answer(
        "Добрый день! Вас приветствует компания BeeinSneakers.\n"
        "Выберите, что хотите заказать:",
        reply_markup=keyboard
    )


# --- Обработчик выбора заказа ---
@dp.callback_query(F.data)
async def handle_order(query: CallbackQuery):
    user = query.from_user
    user_id = user.id
    await query.answer()

    order_text = {
        "order_honey": "Вы выбрали мед фацелиевый.",
        "order_honey2": "Вы выбрали мед майский.",
        "order_honey3": "Вы выбрали мед подсолнечный."
    }

    if query.data in order_text:
        user_data[user_id] = {"choice": order_text[query.data], "step": "awaiting_address"}
        await query.message.answer("Введите название дома и улицу для доставки:")

    elif query.data == "contact_support":
        contact_button = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton("Отправить контакт", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await query.message.answer("Отправьте свой контакт для связи с поддержкой:", reply_markup=contact_button)


# --- Обработчик ввода адреса и email ---
@dp.message(F.text)
async def handle_text_input(message: Message):
    user_id = message.from_user.id

    if user_id in user_data:
        step = user_data[user_id].get("step")

        if step == "awaiting_address":
            user_data[user_id]["address"] = message.text
            user_data[user_id]["step"] = "awaiting_email"
            await message.answer("Введите ваш email:")

        elif step == "awaiting_email":
            user_data[user_id]["email"] = message.text
            user_data[user_id]["step"] = "awaiting_payment"

            order_info = (
                f"**Новый заказ**\n"
                f"📦 {user_data[user_id]['choice']}\n"
                f"📍 Адрес: {user_data[user_id]['address']}\n"
                f"📧 Email: {user_data[user_id]['email']}\n"
                f"👤 @{message.from_user.username or 'Без username'}\n"
                f"🆔 ID: {user_id}"
            )

            # Отправляем админу заказ
            await bot.send_message(chat_id=ADMIN_ID, text=order_info)

            # Добавляем кнопку "Оплатить 1 ⭐️"
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Оплатить 1 ⭐️")]],
                resize_keyboard=True
            )

            await message.answer(
                "Спасибо! Ваш заказ принят. Чтобы завершить оформление, оплатите 1 звезду ⭐️.",
                reply_markup=keyboard
            )


@dp.message(F.text == "Привет 👋")
async def greet_user(message: Message):
    """
    Отвечает "Привет!" и добавляет кнопку "Оплатить 1 ⭐️".
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Оплатить 1 ⭐️")]],
        resize_keyboard=True
    )

    await message.answer("Привет! Как твои дела? 😊", reply_markup=keyboard)


# --- Обработчик кнопки "Оплатить 1 ⭐️" ---
@dp.message(F.text == "Оплатить 1 ⭐️")
async def send_invoice_handler(message: Message):
    """
    Отправка счета на оплату 1 звезды.
    """
    prices = [LabeledPrice(label="XTR", amount=100)]  # 1 звезда (в копейках, 100 = 1 XTR)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Оплатить 1 ⭐️",
                    pay=True
                )
            ]
        ]
    )

    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Оплата одной звезды",
        description="Поддержка бота за 1 звезду!",
        provider_token="",  # Telegram Stars не требует provider_token
        currency="XTR",
        prices=prices,
        payload="one_star_payment",
        reply_markup=keyboard
    )


# --- Подтверждение готовности принять оплату ---
@dp.pre_checkout_query(lambda query: True)
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """
    Подтверждение при оплате.
    """
    await pre_checkout_query.answer(ok=True)


# --- Обработчик успешного платежа ---
@dp.message(lambda message: message.successful_payment)
async def success_payment_handler(message: Message):
    """
    Обработка успешного платежа.
    """
    await message.answer(text="✅ Спасибо за оплату 1 звезды! Вы поддержали бота ⭐️")


# --- Запуск бота ---
async def main():
    logging.basicConfig(level=logging.INFO)
    dp = Dispatcher()
    dp.include_router(dp)  # Включаем обработчики
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
