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

# -- Не менять! --
TOKEN = 'TOKEN'
ADMIN_ID = ID

# -- ВАШИ провайдер-токены (Payment Provider) --
# 1) Для "звезд" (условной валюты XTR). Пример тестового провайдера:
STARS_PROVIDER_TOKEN = "TEST:XXXXXXXXXXXXXXXXXX"

# 2) Для оплаты банковской картой в Telegram (UAH). (Ваш новый LIVE-токен)
CARD_PROVIDER_TOKEN = "5775769170:LIVE:TG_ZbBvIRPjCeC4eUAJ5ccnte0A"

# -- Базовая цена в гривнах --
BASE_PRICE_UAH = 250
# -- Базовое кол-во звезд --
BASE_STARS = 500

# -- Промокоды: ключ = код, значение = скидка (0.10 = 10%) --
PROMO_CODES = {
    'test1': 0.10,
    'test2': 0.15,
    'test3': 0.20,
    'test4': 0.9
}

# -- Ссылки liqpay --
PAYMENT_LINKS = {
    'default': 'https://www.privat24.ua/rd/send_qr/liqpay_static_qr/payment_2602692399.b5ad9288bd59b678c803bd939569ca5766edbcf0abec06bce69d0facbd6dab2f',
    'test1': 'https://www.privat24.ua/rd/send_qr/liqpay_static_qr/payment_2602692938.c676226d0e64afaf48ff1ef47be6b3f3752ad812aa739eb194215713263282a4',
    'test2': 'https://www.privat24.ua/rd/send_qr/liqpay_static_qr/payment_2602693316.16c12f39400fe505f67fc566faae67f1e69092e8428c52cd9b97af175613d5c5',
    'test3': 'https://www.privat24.ua/rd/send_qr/liqpay_static_qr/payment_2602693685.698e97a8b6145e76857e5386de82859e2cd1f136cb75af77ef3725005d71c7a6',
    'test4': 'https://www.privat24.ua/rd/send_qr/liqpay_static_qr/payment_2602694630.5a51c20f143dac182c6f9b6c10abefe58dab444062e29ae3c4775565588513e3'
}

# -- Храним данные пользователя --
user_data = {}


def get_liqpay_link(promo_code: str = None) -> str:
    """
    Возвращает ссылку liqpay, зависящую от промокода.
    Если промокода нет или он невалиден, возвращаем default.
    """
    if promo_code in PAYMENT_LINKS:
        return PAYMENT_LINKS[promo_code]
    return PAYMENT_LINKS['default']


def calculate_discounted_stars(discount: float) -> int:
    """
    Считает, сколько звёзд надо заплатить с учётом скидки.
    BASE_STARS = 500, если скидка 10% => нужно 450 звёзд.
    """
    stars = BASE_STARS * (1 - discount)
    return int(stars)


def calculate_discounted_price_uah(discount: float) -> float:
    """
    Считает, сколько гривен нужно заплатить с учётом скидки.
    BASE_PRICE_UAH = 500, если скидка 10% => 450.0 грн.
    """
    return BASE_PRICE_UAH * (1 - discount)


async def refund(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /refund для возврата звезд
    """
    # Проверяем, является ли пользователь администратором
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Использование: /refund <user_id>")
        return

    try:
        user_id_to_refund = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите правильный ID пользователя.")
        return

    # Проверяем, есть ли данные о пользователе
    if user_id_to_refund not in user_data:
        await update.message.reply_text(f"Пользователь с ID {user_id_to_refund} не найден.")
        return

    # Возвращаем звезды
    user_data[user_id_to_refund]['discount'] = 0.0  # Снимаем скидку
    user_data[user_id_to_refund]['step'] = 'chose_honey'  # Возвращаем к выбору меда

    await update.message.reply_text(f"Звезды для пользователя {user_id_to_refund} были возвращены.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Стартовая команда /start
    """
    keyboard = [
        [InlineKeyboardButton("Заказать мед фацельевый", callback_data='order_honey')],
        [InlineKeyboardButton("Заказать мед майский", callback_data='order_honey2')],
        [InlineKeyboardButton("Заказать мед Подсолнечный", callback_data='order_honey3')],
        [InlineKeyboardButton("Связаться с техподдержкой", callback_data='contact_support')],
        [InlineKeyboardButton("Открыть веб-приложение",
                              web_app=WebAppInfo(url='https://saniok6789.github.io/finalProjekt/'))]
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
            [KeyboardButton(text='Открыть веб страницу',
                            web_app=WebAppInfo(url='https://saniok6789.github.io/finalProjekt/'))]
        ],
        resize_keyboard=True
    )
    await update.message.reply_text(
        "Откройте веб-приложение с помощью кнопки ниже:",
        reply_markup=markup
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {}

    # --- Пользователь выбрал один из видов меда ---
    if query.data in ['order_honey', 'order_honey2', 'order_honey3']:
        choice_text = {
            'order_honey': 'Вы выбрали заказать мед фацельевый',
            'order_honey2': 'Вы выбрали заказать мед майский',
            'order_honey3': 'Вы выбрали заказать мед Подсолнечный'
        }.get(query.data, 'Неизвестный товар.')

        user_data[user_id] = {
            'choice': choice_text,
            'step': 'chose_honey',
            'discount': 0.0  # скидка по умолчанию
        }

        # Предлагаем 4 кнопки:
        keyboard = [
            [
                InlineKeyboardButton("Оплатить звездами", callback_data='pay_stars'),
                InlineKeyboardButton("Оплатить картой (Telegram)", callback_data='pay_card_in_telegram')
            ],
            [
                InlineKeyboardButton("Промокод", callback_data='enter_promo'),
                InlineKeyboardButton("Оплатить liqpay", callback_data='pay_liqpay_link')
            ]
        ]

        text_for_user = (
            f"{choice_text}\n"
            f"Цена без скидки: {BASE_PRICE_UAH} грн (или {BASE_STARS} ⭐️)\n"
            "Выберите способ оплаты:"
        )
        await query.message.reply_text(
            text=text_for_user,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # --- Оплатить звездами ---
    elif query.data == 'pay_stars':
        discount = user_data[user_id].get('discount', 0.0)
        discounted_stars = calculate_discounted_stars(discount)

        user_data[user_id]['step'] = 'awaiting_star_payment'

        title = "Оплата звездами"
        description = f"Оплата за мёд. Скидка: {int(discount * 1)}%"
        currency = "XTR"  # Условная валюта для "звезд"
        prices = [LabeledPrice("⭐️", discounted_stars * 1)]
        payload = "star_payment_payload"

        await context.bot.send_invoice(
            chat_id=user_id,
            title=title,
            description=description,
            provider_token=STARS_PROVIDER_TOKEN,
            currency=currency,
            prices=prices,
            payload=payload
        )

    # --- Оплатить картой в Telegram ---
    elif query.data == 'pay_card_in_telegram':
        discount = user_data[user_id].get('discount', 0.0)
        discounted_price = calculate_discounted_price_uah(discount)
        amount_in_kopecks = int(round(discounted_price * 100))

        user_data[user_id]['step'] = 'awaiting_card_payment'

        title = "Оплата картой (UAH)"
        description = f"Оплата за мёд. Скидка: {int(discount * 100)}%"
        currency = "UAH"
        prices = [LabeledPrice("Мёд", amount_in_kopecks)]
        payload = "card_payment_payload"

        await context.bot.send_invoice(
            chat_id=user_id,
            title=title,
            description=description,
            provider_token=CARD_PROVIDER_TOKEN,
            currency=currency,
            prices=prices,
            payload=payload
        )

    # --- Ввести промокод ---
    elif query.data == 'enter_promo':
        user_data[user_id]['step'] = 'promo'
        await query.message.reply_text("Введите, пожалуйста, ваш промокод:")

    # --- Оплатить liqpay (по ссылке) ---
    elif query.data == 'pay_liqpay_link':
        discount = user_data[user_id].get('discount', 0.0)
        promo_code = user_data[user_id].get('promo_code', None) if discount > 0 else None
        link = get_liqpay_link(promo_code)
        keyboard = [[InlineKeyboardButton("Перейти к оплате liqpay", url=link)]]
        await query.message.reply_text(
            "Оплата через liqpay: После оплаты, пожалуйста, отправьте свой контакт для завершения заказа.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Переходим к шагу для запроса контакта
        user_data[user_id]['step'] = 'awaiting_contact_after_liqpay'


# Обработка контакта после LiqPay
async def handle_contact_after_liqpay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    contact = update.message.contact

    if contact:
        # Уведомляем администратора о том, что человек вероятно оплатил
        user_info = (
            f"User ID: {user.id}\n"
            f"Username: @{user.username if user.username else 'N/A'}\n"
            f"Full Name: {user.full_name}\n"
            f"Phone Number: {contact.phone_number}"
        )
        support_message = f"Пользователь, вероятно, оплатил через LiqPay и запросил завершение заказа:\n\n{user_info}"

        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=support_message)
            await update.message.reply_text("Ваш контакт был успешно отправлен администратору. Ожидайте связи.")
        except Exception as e:
            print(f"Ошибка при отправке сообщения администратору: {e}")
            await update.message.reply_text("Произошла ошибка при отправке данных.")
    else:
        await update.message.reply_text("Ошибка при получении контакта. Попробуйте снова.")


# Обработка сообщений (для промокодов и других сообщений)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id
    text = update.message.text.strip()

    if user_id not in user_data:
        return

    step = user_data[user_id].get('step')

    # --- Пользователь вводит промокод ---
    if step == 'promo':
        promo_code = text
        if promo_code in PROMO_CODES:
            discount = PROMO_CODES[promo_code]
            user_data[user_id]['discount'] = discount
            user_data[user_id]['promo_code'] = promo_code
            # Возвращаемся к состоянию "chose_honey"
            user_data[user_id]['step'] = 'chose_honey'

            discounted_uah = calculate_discounted_price_uah(discount)
            discounted_stars = calculate_discounted_stars(discount)

            # Показываем сообщение о скидке
            await update.message.reply_text(
                f"Промокод принят! Скидка: {int(discount * 100)}%\n"
                f"Новая цена: {discounted_uah:.2f} грн или {discounted_stars} ⭐️"
            )

            # Теперь снова предлагаем все варианты оплаты
            keyboard = [
                [
                    InlineKeyboardButton("Оплатить звездами", callback_data='pay_stars'),
                    InlineKeyboardButton("Оплатить картой (Telegram)", callback_data='pay_card_in_telegram')
                ],
                [
                    InlineKeyboardButton("Оплатить liqpay", callback_data='pay_liqpay_link')
                ]
            ]
            await update.message.reply_text(
                "Выберите способ оплаты:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text("Промокод не найден! Введите заново или выберите другой способ оплаты.")
            user_data[user_id]['step'] = 'chose_honey'


# --- PreCheckout (для всех типов Invoice) ---
async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    await query.answer(ok=True)


# --- Успешная оплата ---
async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_id = user.id

    # Если записи о пользователе нет, пропускаем
    if user_id not in user_data:
        await update.message.reply_text("Спасибо за оплату, но не удалось найти заказ.")
        return

    step = user_data[user_id].get('step')

    if step == 'awaiting_star_payment':
        user_data[user_id]['step'] = 'paid_by_stars_awaiting_address'
        choice = user_data[user_id].get('choice', 'Неизвестный товар')
        discount = user_data[user_id].get('discount', 0.0)

        # Уведомляем админа
        admin_text = (
            f"Пользователь оплатил ЗВЁЗДАМИ!\n\n"
            f"{choice}\n"
            f"Скидка: {int(discount * 100)}%\n"
            f"UserID: {user_id} (@{user.username if user.username else 'no_username'})\n\n"
            "Адрес и email ещё не введены."
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)

        await update.message.reply_text(
            "Оплата успешно получена! Теперь укажите, пожалуйста, адрес доставки (улица, дом и т.п.):"
        )

    elif step == 'awaiting_card_payment':
        user_data[user_id]['step'] = 'paid_by_card_awaiting_address'
        choice = user_data[user_id].get('choice', 'Неизвестный товар')
        discount = user_data[user_id].get('discount', 0.0)

        admin_text = (
            f"Пользователь оплатил КАРТОЙ!\n\n"
            f"{choice}\n"
            f"Скидка: {int(discount * 100)}%\n"
            f"UserID: {user_id} (@{user.username if user.username else 'no_username'})\n\n"
            "Адрес и email ещё не введены."
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)

        await update.message.reply_text(
            "Оплата успешно получена! Теперь укажите, пожалуйста, адрес доставки (улица, дом и т.п.):"
        )
    else:
        await update.message.reply_text("Спасибо за оплату, но заказ не найден. Свяжитесь с поддержкой.")


def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    # /start и /bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("bot", open_webapp))

    # Обработчик команды /refund
    application.add_handler(CommandHandler("refund", refund))

    # Инлайн-кнопки
    application.add_handler(CallbackQueryHandler(button))

    # Текстовые сообщения (промокоды, адреса, e-mail):
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Контакты (техподдержка)
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact_after_liqpay))

    # Платежи (Invoice)
    application.add_handler(PreCheckoutQueryHandler(precheckout_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))

    print("Бот запущен! 🚀")
    application.run_polling()

if __name__ == "__main__":
    main()

