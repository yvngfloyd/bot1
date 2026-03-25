from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import (
    BOT_TOKEN,
    BOT_ACTIVE_END_HOUR,
    BOT_ACTIVE_START_HOUR,
    MOCK_SLOTS,
    SERVICES,
    TIMEZONE,
)
from db import init_db, save_booking, save_callback, save_question


MAIN_MENU, CHOOSE_SERVICE, CHOOSE_SLOT, ENTER_NAME, ENTER_PHONE, ASK_QUESTION, CALLBACK_NAME, CALLBACK_PHONE = range(8)


def is_bot_active_now() -> bool:
    now = datetime.now(ZoneInfo(TIMEZONE))
    hour = now.hour

    start_h = BOT_ACTIVE_START_HOUR
    end_h = BOT_ACTIVE_END_HOUR

    # Если диапазон переходит через полночь, например 20 -> 9
    if start_h > end_h:
        return hour >= start_h or hour < end_h

    # Обычный дневной диапазон, например 9 -> 18
    return start_h <= hour < end_h


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["Записаться", "Свободные окна"],
            ["Задать вопрос", "Обратный звонок"],
        ],
        resize_keyboard=True,
    )


def services_keyboard() -> ReplyKeyboardMarkup:
    rows = [[service] for service in SERVICES]
    rows.append(["Назад"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def slots_keyboard(service: str) -> ReplyKeyboardMarkup:
    rows = [[slot] for slot in MOCK_SLOTS.get(service, [])]
    rows.append(["Назад"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_bot_active_now():
        await update.message.reply_text(
            "Сейчас бот не работает\n"
            f"Активные часы: {BOT_ACTIVE_START_HOUR}:00 - {BOT_ACTIVE_END_HOUR}:00\n"
            "Попробуйте позже",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text(
        "Здравствуйте\n"
        "Я помогу выбрать свободное окно, записаться или оставить вопрос",
        reply_markup=main_menu_keyboard(),
    )
    return MAIN_MENU


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == "Записаться":
        await update.message.reply_text(
            "Выберите услугу",
            reply_markup=services_keyboard(),
        )
        return CHOOSE_SERVICE

    if text == "Свободные окна":
        await update.message.reply_text(
            "Выберите услугу, и я покажу ближайшие свободные окна",
            reply_markup=services_keyboard(),
        )
        return CHOOSE_SERVICE

    if text == "Задать вопрос":
        await update.message.reply_text(
            "Напишите ваш вопрос одним сообщением",
            reply_markup=ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True),
        )
        return ASK_QUESTION

    if text == "Обратный звонок":
        await update.message.reply_text(
            "Как вас зовут",
            reply_markup=ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True),
        )
        return CALLBACK_NAME

    await update.message.reply_text(
        "Выберите действие из меню",
        reply_markup=main_menu_keyboard(),
    )
    return MAIN_MENU


async def choose_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == "Назад":
        await update.message.reply_text(
            "Возвращаю в меню",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN_MENU

    if text not in SERVICES:
        await update.message.reply_text(
            "Выберите услугу из списка",
            reply_markup=services_keyboard(),
        )
        return CHOOSE_SERVICE

    context.user_data["service"] = text
    slots = MOCK_SLOTS.get(text, [])

    if not slots:
        await update.message.reply_text(
            "По этой услуге пока нет свободных окон\n"
            "Можете выбрать другую услугу или оставить заявку на обратный звонок",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN_MENU

    await update.message.reply_text(
        f"Свободные окна по услуге «{text}»",
        reply_markup=slots_keyboard(text),
    )
    return CHOOSE_SLOT


async def choose_slot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    service = context.user_data.get("service", "")

    if text == "Назад":
        await update.message.reply_text(
            "Выберите услугу",
            reply_markup=services_keyboard(),
        )
        return CHOOSE_SERVICE

    valid_slots = MOCK_SLOTS.get(service, [])
    if text not in valid_slots:
        await update.message.reply_text(
            "Выберите свободное окно из списка",
            reply_markup=slots_keyboard(service),
        )
        return CHOOSE_SLOT

    context.user_data["slot"] = text

    await update.message.reply_text(
        "Как вас зовут",
        reply_markup=ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True),
    )
    return ENTER_NAME


async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == "Назад":
        service = context.user_data.get("service", "")
        await update.message.reply_text(
            "Выберите окно",
            reply_markup=slots_keyboard(service),
        )
        return CHOOSE_SLOT

    context.user_data["client_name"] = text.strip()

    await update.message.reply_text(
        "Укажите телефон",
        reply_markup=ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True),
    )
    return ENTER_PHONE


async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == "Назад":
        await update.message.reply_text(
            "Как вас зовут",
            reply_markup=ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True),
        )
        return ENTER_NAME

    context.user_data["phone"] = text.strip()

    user = update.effective_user
    service = context.user_data["service"]
    slot = context.user_data["slot"]
    client_name = context.user_data["client_name"]
    phone = context.user_data["phone"]

    save_booking(
        user_id=user.id,
        username=user.username or "",
        service=service,
        slot=slot,
        client_name=client_name,
        phone=phone,
    )

    await update.message.reply_text(
        "Готово, заявка на запись сохранена\n\n"
        f"Услуга: {service}\n"
        f"Окно: {slot}\n"
        f"Имя: {client_name}\n"
        f"Телефон: {phone}\n\n"
        "Это тестовый режим без CRM\n"
        "На следующем этапе сюда подключим YCLIENTS",
        reply_markup=main_menu_keyboard(),
    )

    context.user_data.clear()
    return MAIN_MENU


async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == "Назад":
        await update.message.reply_text(
            "Возвращаю в меню",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN_MENU

    user = update.effective_user
    save_question(
        user_id=user.id,
        username=user.username or "",
        question=text.strip(),
    )

    await update.message.reply_text(
        "Вопрос сохранён\n"
        "На следующем этапе можно будет пересылать такие вопросы администратору",
        reply_markup=main_menu_keyboard(),
    )
    return MAIN_MENU


async def callback_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == "Назад":
        await update.message.reply_text(
            "Возвращаю в меню",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN_MENU

    context.user_data["callback_name"] = text.strip()

    await update.message.reply_text(
        "Укажите телефон для обратного звонка",
        reply_markup=ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True),
    )
    return CALLBACK_PHONE


async def callback_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == "Назад":
        await update.message.reply_text(
            "Как вас зовут",
            reply_markup=ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True),
        )
        return CALLBACK_NAME

    user = update.effective_user
    client_name = context.user_data.get("callback_name", "")
    phone = text.strip()

    save_callback(
        user_id=user.id,
        username=user.username or "",
        client_name=client_name,
        phone=phone,
    )

    await update.message.reply_text(
        "Заявка на обратный звонок сохранена",
        reply_markup=main_menu_keyboard(),
    )

    context.user_data.clear()
    return MAIN_MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Сценарий сброшен",
        reply_markup=main_menu_keyboard(),
    )
    return MAIN_MENU


def build_application() -> Application:
    application = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],
        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu),
            ],
            CHOOSE_SERVICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_service),
            ],
            CHOOSE_SLOT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_slot),
            ],
            ENTER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name),
            ],
            ENTER_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone),
            ],
            ASK_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_question),
            ],
            CALLBACK_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, callback_name),
            ],
            CALLBACK_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, callback_phone),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        allow_reentry=True,
    )

    application.add_handler(conv)
    return application


if __name__ == "__main__":
    if not BOT_TOKEN:
        raise ValueError("Не найден BOT_TOKEN в .env")

    init_db()
    app = build_application()
    app.run_polling()
