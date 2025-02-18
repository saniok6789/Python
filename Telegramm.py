import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Токен бота
TOKEN = '6550425386:AAG_m9QuTmE1PR_a7wLdxXjxg7Sfh_wtoqA'
ADMIN_ID = 1763797493

# Цены
BASE_PRICE = 250

# Промокоды
PROMO_CODES = {'test1': 0.10, 'test2': 0.15, 'test3': 0.20}

# Оплата
PAYMENT_LINKS = {
    'default': 'https://www.ipay.ua/ru/constructor/pz6lelpv',
    'test1': 'https://www.ipay.ua/ru/constructor/1ygfunlz',
    'test2': 'https://www.ipay.ua/ru/constructor/ewvsmnwv',
    'test3': 'https://www.ipay.ua/ru/constructor/qg2dke1m'
}

# Данные пользователей
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Заказать мед фацельевый", callback_data='order_honey')],
        [InlineKeyboardButton("Заказать мед майский", callback_data='order_honey2')],
        [InlineKeyboardButton("Заказать мед Подсолнечный", callback_data='order_honey3')],
        [InlineKeyboardButton("Связаться с техподдержкой", callback_data='contact_support')],
        [InlineKeyboardButton("Открыть веб-приложение", web_app=WebAppInfo(url='https://saniok6789.github.io/finalProjekt/'))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Добрый день! Вас приветствует компания BeeinSneakers. Что бы вы хотели заказать?',
        reply_markup=reply_markup
    )

async def open_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='Открыть веб страницу', web_app=WebAppInfo(url='https://saniok6789.github.io/finalProjekt/'))]],
        resize_keyboard=True
    )
    await update.message.reply_text("Откройте веб-приложение с помощью кнопки ниже:", reply_markup=markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = query.from_user
    if query.data in ['order_honey', 'order_honey2', 'order_honey3']:
        user_choice = {
            'order_honey': 'Вы выбрали заказать мед фацельевый.',
            'order_honey2': 'Вы выбрали заказать мед майский.',
            'order_honey3': 'Вы выбрали заказать мед Подсолнечный.'
        }.get(query.data, 'Неправильный выбор.')

        user_data[user.id] = {'choice': user_choice, 'step': 'awaiting_address'}
        await query.message.reply_text("Введите название дома и улицу, куда нужно доставить мед:")

    elif query.data == 'enter_promo':
        user_data[user.id] = {'step': 'promo'}
        await query.message.reply_text("Введите пожалуйста ваш промокод:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id

    if user_id in user_data:
        step = user_data[user_id].get('step')

        if step == 'awaiting_address':
            user_data[user_id]['address'] = update.message.text
            user_data[user_id]['step'] = 'awaiting_email'
            await update.message.reply_text("Введите ваш email:")

        elif step == 'awaiting_email':
            user_data[user_id]['email'] = update.message.text
            user_data[user_id]['step'] = 'completed'
            user_choice = user_data[user_id]['choice']
            address = user_data[user_id]['address']
            email = user_data[user_id]['email']
            order_info = f"Заказ: {user_choice}\nАдрес: {address}\nEmail: {email}"
            await context.bot.send_message(chat_id=ADMIN_ID, text=order_info)
            await update.message.reply_text(
                f"Ваш заказ принят! Оплатите {BASE_PRICE} грн или введите промокод для скидки.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Промокод", callback_data='enter_promo')],
                    [InlineKeyboardButton("ОПЛАТИТЬ", url=PAYMENT_LINKS['default'])]
                ])
            )

        elif step == 'promo':
            promo_code = update.message.text
            if promo_code in PROMO_CODES:
                discount = PROMO_CODES[promo_code]
                discounted_price = BASE_PRICE * (1 - discount)
                await update.message.reply_text(
                    f"У вас скидка {discount * 100}%. Цена со скидкой: {discounted_price:.2f} грн",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("ОПЛАТИТЬ", url=PAYMENT_LINKS[promo_code])]
                    ])
                )
            else:
                await update.message.reply_text("Промокод не найден!")
            user_data.pop(user_id)

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("bot", open_webapp))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен! 🚀")
    application.run_polling()

if __name__ == "__main__":
    main()
