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

# "Тестовый" provider_token для оплаты звездами (замените при необходимости на реальный)
PAYMENT_PROVIDER_TOKEN = "TEST:XXXXXXXXXXXXXXXX"

# Допустим, у нас есть базовая цена в гривнах (для информативного сообщения)
BASE_PRICE_UAH = 250

# Допустим, базовое количество "звёзд" за этот товар = 500
BASE_STARS = 500

# Промокоды и скидки
PROMO_CODES = {
    'test1': 0.10,  # 10%
    'test2': 0.15,  # 15%
    'test3': 0.20   # 20%
}

# Ссылки для оплаты через iPay
# (для каждого промокода - своя ссылка c учётом скидки).
PAYMENT_LINKS = {
    'default': 'https://www.ipay.ua/ru/constructor/pz6lelpv',
    'test1': 'https://www.ipay.ua/ru/constructor/1ygfunlz',
    'test2': 'https://www.ipay.ua/ru/constructor/ewvsmnwv',
    'test3': 'https://www.ipay.ua/ru/constructor/qg2dke1m'
}

# Храним данные о пользователях и заказах
user_data = {}

def get_ipay_link(promo_code: str = None) -> str:
    """
    Возвращает ссылку iPay, зависящую от промокода.
    Если промокода нет или он невалиден, возвращаем default.
    """
    if promo_code in PAYMENT_LINKS:
        return PAYMENT_LINKS[promo_code]
    return PAYMENT_LINKS['default']


def calculate_discounted_stars(discount: float) -> int:
    """
    Считает, сколько звезд надо заплатить с учётом скидки.
    Возвращает целое количество звёзд (округляется вниз).
    """
    # Например, BASE_STARS = 500, скидка = 0.1 => 450 звёзд
    stars = BASE_STARS * (1 - discount)
    return int(stars)  # округляем до целого


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

    # Если пользователь раньше не выбирал товар, и вдруг нажал кнопку...
    if user_id not in user_data:
        user_data[user_id] = {}

    # --- Пользователь выбирает один из видов меда ---
    if query.data in ['order_honey', 'order_honey2', 'order_honey3']:
        # Сохраняем, какой мед выбрал пользователь (для информации)
        user_choice_text = {
            'order_honey': 'Вы выбрали заказать мед фацельевый',
            'order_honey2': 'Вы выбрали заказать мед майский',
            'order_honey3': 'Вы выбрали заказать мед Подсолнечный'
        }.get(query.data, 'Неправильный выбор.')

        user_data[user_id] = {
            'choice': user_choice_text,
            'step': 'chose_honey',  # Пользователь выбрал мед, ждем способ оплаты
            'discount': 0.0         # По умолчанию скидки нет
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
            text=f"{user_choice_text}\nЦена без скидки: {BASE_PRICE_UAH} грн (или {BASE_STARS} ⭐️)\n\nВыберите способ оплаты:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # --- Пользователь хочет оплатить звездами (без промокода) ---
    elif query.data == 'pay_with_stars':
        # Если промокода нет, discount=0
        discount = user_data[user_id].get('discount', 0.0)
        discounted_stars = calculate_discounted_stars(discount)

        user_data[user_id]['step'] = 'awaiting_star_payment'

        title = "Оплата звездами"
        description = f"Оплата за мёд. Скидка: {int(discount*1)}%"
        payload = "star_payment_payload"
        currency = "XTR"  # Условная "звёздная" валюта
        # discounted_stars * 100 => перевод звезд в «суб-единицы»
        prices = [LabeledPrice("⭐️", discounted_stars * 1)]

        await context.bot.send_invoice(
            chat_id=user_id,
            title=title,
            description=description,
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency=currency,
            prices=prices,
            payload=payload
        )
        return

    # --- Пользователь хочет ввести промокод ---
    elif query.data == 'enter_promo':
        user_data[user_id]['step'] = 'promo'
        await query.message.reply_text("Введите, пожалуйста, ваш промокод:")
        return

    # --- Пользователь хочет оплатить товар по ссылке (iPay) ---
    elif query.data == 'pay_with_card':
        # Допустим, если промокод не введён, открываем default ссылку.
        discount = user_data[user_id].get('discount', 0.0)
        if discount and discount > 0:
            # Если вдруг скидка есть, значит ранее уже ввели промокод
            # и в user_data[user_id]['promo_code'] лежит код
            promo_code = user_data[user_id].get('promo_code', None)
            link = get_ipay_link(promo_code)
        else:
            # Если нет скидки, берём ссылку default
            link = get_ipay_link(None)

        # Отправим кнопку с url. Нажатие «перебросит» на сайт.
        keyboard = [[InlineKeyboardButton("Перейти на сайт iPay", url=link)]]
        await query.message.reply_text(
            "Для оплаты нажмите кнопку ниже:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # --- Пользователь хочет оплатить через iPay по скидке (если так решили делать доп. кнопку) ---
    elif query.data == 'pay_ipay_discount':
        # Сюда мы попадаем, если пользователь ввел промокод и выбрал оплату iPay со скидкой
        promo_code = user_data[user_id].get('promo_code', None)
        link = get_ipay_link(promo_code)  # берем конкретную ссылку под промокод
        keyboard = [[InlineKeyboardButton("Оплатить iPay (со скидкой)", url=link)]]
        await query.message.reply_text(
            "Нажмите, чтобы оплатить iPay со скидкой:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
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
    Обработка текстовых сообщений (промокод, адрес, email и т.д.)
    """
    user = update.message.from_user
    user_id = user.id
    text = update.message.text.strip()

    if user_id not in user_data:
        return  # Нет данных о пользователе, пропускаем

    step = user_data[user_id].get('step')

    # --- Пользователь вводит промокод ---
    if step == 'promo':
        promo_code = text
        if promo_code in PROMO_CODES:
            discount = PROMO_CODES[promo_code]
            user_data[user_id]['discount'] = discount
            user_data[user_id]['promo_code'] = promo_code
            user_data[user_id]['step'] = 'after_promo'

            discounted_uah = BASE_PRICE_UAH * (1 - discount)
            discounted_stars = calculate_discounted_stars(discount)
            await update.message.reply_text(
                f"Промокод принят! Скидка: {int(discount*100)}%\n\n"
                f"Новая цена: {discounted_uah:.2f} грн или {discounted_stars} ⭐️\n\n"
                "Выберите, как хотите оплатить:"
            )
            # Показываем две кнопки: оплатить звёздами по скидке, оплатить iPay по скидке
            keyboard = [
                [InlineKeyboardButton("Оплатить звездами (со скидкой)", callback_data='pay_with_stars')],
                [InlineKeyboardButton("Оплатить iPay (со скидкой)", callback_data='pay_ipay_discount')]
            ]
            await update.message.reply_text(
                "Выберите способ оплаты:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Промокод не найден, сбрасываем состояние
            await update.message.reply_text("Промокод не найден! Попробуйте снова или выберите другой способ оплаты.")
            user_data[user_id]['step'] = 'chose_honey'  # Возвращаем в состояние выбора оплаты
        return

    # --- Если пользователь оплатил звездами (в хендлере) и теперь просим адрес ---
    if step == 'paid_by_stars_awaiting_address':
        user_data[user_id]['address'] = text
        user_data[user_id]['step'] = 'paid_by_stars_awaiting_email'
        await update.message.reply_text("Введите ваш e-mail:")
        return

    # --- Если пользователь уже ввёл адрес, теперь ждём e-mail ---
    if step == 'paid_by_stars_awaiting_email':
        user_data[user_id]['email'] = text
        user_data[user_id]['step'] = 'completed'

        choice = user_data[user_id]['choice']
        address = user_data[user_id]['address']
        email = user_data[user_id]['email']
        discount = user_data[user_id].get('discount', 0.0)

        # Формируем сообщение для админа
        order_info = (
            f"Заказ ОПЛАЧЕН ЗВЁЗДАМИ!\n\n"
            f"{choice}\n"
            f"Скидка: {int(discount*100)}%\n"
            f"Адрес: {address}\n"
            f"Email: {email}\n"
            f"UserID: {user_id} (@{user.username if user.username else 'no_username'})"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=order_info)

        # Уведомляем пользователя, что заказ оформлен
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
    await query.answer(ok=True)


# --- Хендлер успешного платежа ---
async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Пользователь успешно оплатил «звёздами».
    """
    user = update.message.from_user
    user_id = user.id

    if user_id in user_data and user_data[user_id].get('step') == 'awaiting_star_payment':
        user_data[user_id]['step'] = 'paid_by_stars_awaiting_address'
        choice = user_data[user_id].get('choice', 'Неизвестный товар')
        discount = user_data[user_id].get('discount', 0.0)

        # Уведомляем админа, что пришла оплата звездами (но адреса ещё нет)
        admin_text = (
            f"Пользователь оплатил ЗВЁЗДАМИ!\n\n"
            f"{choice}\n"
            f"Скидка: {int(discount*100)}%\n"
            f"UserID: {user_id} (@{user.username if user.username else 'no_username'})\n\n"
            "Адрес и email ещё не введены."
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)

        # Просим пользователя ввести адрес доставки
        await update.message.reply_text(
            "Оплата успешно получена! Теперь укажите, пожалуйста, адрес доставки (улица, дом и т.п.):"
        )
    else:
        # Если успешная оплата прилетела не в нужном состоянии
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

