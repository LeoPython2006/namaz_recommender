# Импортируем необходимые модули из библиотеки python-telegram-bot
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler
)
import logging  # Модуль для логирования
import asyncio  # Модуль для асинхронного программирования
import requests  # Модуль для HTTP-запросов
from datetime import datetime, timezone  # Модуль для работы с датой и временем

# Настройка логирования для отслеживания работы бота
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)  # Создаем логгер

# Создаем клавиатуру для главного меню с двумя кнопками
main_keyboard = ReplyKeyboardMarkup(
    [["/ask", "/help"]],  # Кнопки команд
    resize_keyboard=True,  # Автоматически подгонять размер
    one_time_keyboard=False,  # Клавиатура остается после использования
)

# Токен бота (в реальном проекте нужно использовать переменные окружения)
TOKEN = "7732002021:AAE2Bm08v2RoxRDsvyAy7HyjfREr05VenhQ"

# Определяем состояния для ConversationHandler
START, GET_NAME = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start - начало работы с ботом"""
    await update.message.reply_text(
        "Привет! Я первая версия бота для нашего супер проекта про рекомендательные системы",
        reply_markup=main_keyboard,
    )

    # Проверяем, зарегистрирован ли пользователь в базе данных
    api_check_user = f"https://swpdb-production.up.railway.app/users/{update.effective_user.id}/"
    if requests.get(api_check_user).status_code == 200:
        await update.message.reply_text(
            "Вы уже зарегистрированы!",
            reply_markup=main_keyboard,
        )
        return ConversationHandler.END

    # Если пользователь не зарегистрирован, просим ввести имя
    await update.message.reply_text(
        "Пожалуйста, введите ваше имя: ",
        reply_markup=main_keyboard,
    )
    return GET_NAME  # Переходим в состояние ожидания имени


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик для получения имени пользователя"""
    user_name = update.message.text
    context.user_data['name'] = user_name  # Сохраняем имя в контексте

    await update.message.reply_text(
        f"Отлично, {user_name}! Теперь вы можете пользоваться ботом.",
        reply_markup=main_keyboard,
    )

    # Отправляем данные пользователя на сервер
    payload_name_json = {
        "_id": update.effective_user.id,
        "name": user_name,
    }
    api_create_user = "https://swpdb-production.up.railway.app/users/"
    response_name = requests.post(api_create_user, json=payload_name_json)

    return ConversationHandler.END  # Завершаем диалог


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик отмены регистрации"""
    await update.message.reply_text(
        "Отмена",
        reply_markup=main_keyboard,
    )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help - вывод справки"""
    await update.message.reply_text(
        "Доступные команды:\n"
        "/ask - задать вопрос\n"
        "/help - основные правила пользования ботом\n"
        "/reload - обновить чат\n",
        reply_markup=main_keyboard,
    )


# Состояние для обработки вопросов
WAITING_MESSAGE = 1
conv_id = ""


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /ask - начало диалога"""
    context.user_data['last_message'] = None

    # Создаем специальную клавиатуру с кнопкой "Отмена"
    ask_keyboard = ReplyKeyboardMarkup(
        [["Отмена"]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.message.reply_text(
        "Напишите свой запрос! Я постараюсь помочь вам!",
        reply_markup=ask_keyboard
    )

    # Создаем новую беседу в базе данных
    api_create_conv = "https://swpdb-production.up.railway.app/conversations/"
    payload_create_conv = {
        "user_id": update.effective_user.id,
        "messages": [
            {
                "sender": "user",
                "text": "STARTING_MESSAGE",
                "time": "2025-06-22T19:52:30.467Z"
            }
        ]
    }
    response_create_conv = requests.post(api_create_conv, json=payload_create_conv)
    response_create_conv_json = response_create_conv.json()
    context.user_data['conv_id'] = response_create_conv_json.get("_id")

    return WAITING_MESSAGE  # Переходим в состояние ожидания сообщения


async def ask_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик текстовых сообщений в режиме /ask"""
    user_text = update.message.text
    context.user_data['last_message'] = user_text

    # Отправляем эхо-ответ
    await update.message.reply_text(
        f"ваш текст: {user_text}",
        reply_markup=main_keyboard
    )

    # Сохраняем сообщение в базе данных
    api_add_message = f"https://swpdb-production.up.railway.app/conversations/{context.user_data['conv_id']}/messages"
    payload_add_message = {
        "sender": "user",
        "text": user_text,
        "time": update.message.date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    }
    response_add_message = requests.post(api_add_message, json=payload_add_message)

    return WAITING_MESSAGE  # Остаемся в том же состоянии


def register_handlers(application):
    """Функция регистрации всех обработчиков команд"""
    # Регистрируем простые команды
    application.add_handler(CommandHandler("help", help_command))

    # Регистрируем ConversationHandler для команды /start
    conv_handler_start = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_name
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Регистрируем ConversationHandler для команды /ask
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("ask", ask)],
        states={
            WAITING_MESSAGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    ask_handler
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^Отмена$"), cancel),
        ],
    )

    # Добавляем обработчики в приложение
    application.add_handler(conv_handler)
    application.add_handler(conv_handler_start)


async def main():
    """Основная функция запуска бота"""
    # Создаем приложение и передаем токен бота
    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики команд
    register_handlers(application)

    # Инициализируем и запускаем бота в режиме polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    logger.info("Бот запущен и работает...")

    # Бесконечный цикл для поддержания работы бота
    while True:
        await asyncio.sleep(3600)  # Приостанавливаем выполнение на 1 час


if __name__ == '__main__':
    try:
        # Запускаем основную функцию
        asyncio.run(main())
    except KeyboardInterrupt:
        # Обрабатываем прерывание с клавиатуры
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        # Логируем другие ошибки
        logger.error(f"Ошибка в работе бота: {e}")