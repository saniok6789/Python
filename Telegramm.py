import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
    LabeledPrice
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
    ContextTypes
)

# Токен бота (НЕ МЕНЯТЬ)
TOKEN = '6550425386:AAG_m9QuTmE1PR_a7wLdxXjxg7Sfh_wtoqA'
# ID администратора (НЕ МЕНЯТЬ)
ADMIN_ID = 1763797493

# "Тестовый" provider_token для оплаты (замените при необходимости на рабочий)
PAYMENT_PROVIDER_TOKEN = "TEST:XXXXXXXXXXXXXX"

# Базовая цена (гривны)
BASE_PRICE = 250

# Промокоды
PROMO_CODES = {
    'test1': 0.10,
    'test2': 0.15,
    'test3': 0.20
}

# Ссылки для оплаты через iPay
PAYMENT_LINKS = {
    'default': 'https://www.ipay.ua/ru/constructor/pz6lelpv',
    'test1': 'https://www.ipay.ua/ru/constructor/1ygfunlz',
    'test2': 'https://www.ipay.ua/ru/constructor/ewvsmnwv',
    'test3': 'https://www.ipay.ua/ru/constructor/qg2dke1m'
}

# Храним данные о пользователях и заказах
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Стартовая команда /start
    """
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
    """
    Команда /bot, которая выводит кнопку для открытия веб-приложения
    """
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Открыть веб страницу', web_app=WebAppInfo(url='https://saniok6789.github.io/finalProjekt/'))]
        ],
        resize_keyboard=True
    )
    await update.message.reply_text(
        "Откройте веб-приложение с помощью кнопки ниже:",
        reply_markup=markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработка нажатий на Inline-кнопки
    """
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id

    # --- Пользователь выбирает один из видов меда ---
    if query.data in ['order_honey', 'order_honey2', 'order_honey3']:
        # Сохраняем, какой мед выбрал пользователь
        user_choice_text = {
            'order_honey': 'Вы выбрали заказать мед фацельевый.',
            'order_honey2': 'Вы выбрали заказать мед майский.',
            'order_honey3': 'Вы выбрали заказать мед Подсолнечный.'
        }.get(query.data, 'Неправильный выбор.')

        user_data[user_id] = {
            'choice': user_choice_text,
            'step': 'chose_honey'  # Пользователь выбрал мед, ждем способ оплаты
        }

        # Предлагаем варианты оплаты
        keyboard = [
            [
                InlineKeyboardButton("Оплатить звездами", callback_data='pay_with_stars'),
                InlineKeyboardButton("Промокод", callback_data='enter_promo'),
            ],
            [
                InlineKeyboardButton("Оплатить товар (iPay)", callback_data='pay_with_card')
            ]
        ]
        await query.message.reply_text(
            text=f"{user_choice_text}\nВыберите способ оплаты:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # --- Пользователь решил оплатить звездами ---
    elif query.data == 'pay_with_stars':
        # Сохраняем, что далее идёт процесс оплаты звездами
        user_data[user_id]['step'] = 'awaiting_star_payment'

        # Отправляем invoice (пример на 1 звезду = 100 «внутренних единиц»)
        # В реальном боте тут должен быть реальный provider_token и валюта "UAH"/"USD"/и т.д.
        # Но для демонстрации предполагаем "XTR" (условная "звездная" валюта).
        title = "Оплата звездами"
        description = "Оплата за мед (пример)."
        payload = "star_payment_payload"  # Произвольная строка, которая вернется в PreCheckoutQuery
        currency = "XTR"  # Фиктивная "валюта"
        prices = [LabeledPrice("1 ⭐️", 500)]  # 100 единиц = 1 звезда (пример)

        await context.bot.send_invoice(
            chat_id=user_id,
            title=title,
            description=description,
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency=currency,
            prices=prices,
            payload=payload
        )
        # Пользователю отобразится кнопка "Pay"
        return

    # --- Пользователь хочет ввести промокод ---
    elif query.data == 'enter_promo':
        user_data[user_id]['step'] = 'promo'
        await query.message.reply_text("Введите, пожалуйста, ваш промокод:")
        return

    # --- Пользователь хочет оплатить товар по ссылке (iPay) ---
    elif query.data == 'pay_with_card':
        # Считаем, что без промокода = полная цена
        # Если промокод был введён ранее (в теории), можно учитывать user_data[user_id].get('discount')
        # Но в данном упрощенном коде мы считаем, что промокод не вводился.
        await query.message.reply_text(
            text=f"Перейдите по ссылке для оплаты: {PAYMENT_LINKS['default']}"
        )
        # После оплаты пользователь может вернуться и сообщить об оплате, если нужно.
        # Логика зависит от ваших бизнес-процессов.
        return

    # --- Обработка обращения в техподдержку ---
    elif query.data == 'contact_support':
        contact_button = ReplyKeyboardMarkup(
            [[KeyboardButton("Отправить свой контакт", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await query.message.reply_text(
            "Пожалуйста, отправьте свой контакт для связи с технической поддержкой:",
            reply_markup=contact_button
        )
        return


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработка текстовых сообщений (адрес, email, промокод и т.д.)
    """
    user = update.message.from_user
    user_id = user.id
    text = update.message.text

    if user_id not in user_data:
        return  # Нет данных о пользователе, пропускаем

    step = user_data[user_id].get('step')

    # --- Пользователь вводит промокод ---
    if step == 'promo':
        promo_code = text.strip()
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
        # Сбрасываем состояние пользователя (чтобы заново не спрашивать)
        user_data.pop(user_id, None)
        return

    # --- Если пользователь уже УСПЕШНО ОПЛАТИЛ звездами, просим ввести адрес ---
    if step == 'paid_by_stars_awaiting_address':
        user_data[user_id]['address'] = text
        user_data[user_id]['step'] = 'paid_by_stars_awaiting_email'
        await update.message.reply_text("Введите ваш e-mail:")
        return

    # --- Если пользователь ввёл адрес, теперь ждём e-mail ---
    if step == 'paid_by_stars_awaiting_email':
        user_data[user_id]['email'] = text
        user_data[user_id]['step'] = 'completed'

        # Уведомляем админа, что пользователь сообщил адрес
        choice = user_data[user_id]['choice']
        address = user_data[user_id]['address']
        email = user_data[user_id]['email']

        # Формируем сообщение для админа
        order_info = (
            f"Заказ ОПЛАЧЕН ЗВЕЗДАМИ!\n\n"
            f"{choice}\n"
            f"Адрес: {address}\n"
            f"Email: {email}\n"
            f"UserID: {user_id} (@{user.username if user.username else 'no_username'})"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=order_info)

        # Уведомляем пользователя, что заказ принят
        await update.message.reply_text("Спасибо! Ваш заказ оформлен. Ожидайте доставки.")

        # Очищаем данные
        user_data.pop(user_id, None)
        return


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработка контакта, который пользователь отправляет для связи с техподдержкой
    """
    contact = update.message.contact
    user = update.message.from_user

    if contact:
        user_info = (
            f"User ID: {user.id}\n"
            f"Username: @{user.username if user.username else 'N/A'}\n"
            f"Full Name: {user.full_name}\n"
            f"Phone Number: {contact.phone_number}"
        )
        support_message = f"Пользователь запросил связь с техподдержкой:\n\n{user_info}"

        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=support_message)
            await update.message.reply_text("Ваш контакт был успешно отправлен администратору. Ожидайте связи.")
        except Exception as e:
            print(f"Ошибка при отправке сообщения администратору: {e}")
            await update.message.reply_text("Произошла ошибка при отправке данных.")
    else:
        await update.message.reply_text("Ошибка при получении контакта.")


# --- Хендлер предварительной проверки платежа (Invoice) ---
async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    # Допустим, если что-то пошло не так, отвечаем ok=False
    await query.answer(ok=True)


# --- Хендлер успешного платежа ---
async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Пользователь успешно оплатил «звёздами».
    """
    user = update.message.from_user
    user_id = user.id

    # Помечаем в user_data, что пользователь оплатил звездами
    if user_id in user_data and user_data[user_id].get('step') == 'awaiting_star_payment':
        user_data[user_id]['step'] = 'paid_by_stars_awaiting_address'

        # Уведомляем админа, что пришла оплата звездами (без адреса, т.к. ещё не спрашивали)
        choice = user_data[user_id]['choice']
        admin_text = (
            f"Пользователь оплатил ЗВЁЗДАМИ!\n\n"
            f"{choice}\n"
            f"UserID: {user_id} (@{user.username if user.username else 'no_username'})\n\n"
            "Адрес и email ещё не введены."
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)

        # Просим пользователя ввести адрес доставки
        await update.message.reply_text(
            "Оплата успешно получена! Теперь укажите, пожалуйста, адрес доставки (улица, дом и т.п.):"
        )

    else:
        # Если вдруг сообщение о successful_payment пришло не в нужном состоянии
        await update.message.reply_text("Спасибо за оплату, но мы не распознали заказ. Свяжитесь с поддержкой.")


def main() -> None:
    # Создаем экземпляр приложения и регистрируем хендлеры
    application = ApplicationBuilder().token(TOKEN).build()

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("bot", open_webapp))

    # Inline-кнопки (CallbackQuery)
    application.add_handler(CallbackQueryHandler(button))

    # Текстовые сообщения (промокоды, адреса, email и т.д.)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Обработчик контактов (для техподдержки)
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    # Платежи (Invoice handlers)
    application.add_handler(PreCheckoutQueryHandler(precheckout_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))

    print("Бот запущен! 🚀")
    application.run_polling()


if __name__ == "__main__":
    main()

