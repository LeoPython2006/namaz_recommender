from fastapi import FastAPI, Request
from datetime import timezone
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes, ConversationHandler,
)
import os
import uvicorn  # Добавляем для запуска сервера
import httpx



app = FastAPI()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Пример: https://your-project.up.railway.app

# Инициализация бота
application = Application.builder().token(TOKEN).build()

# Клавиатура для главного меню
main_keyboard = ReplyKeyboardMarkup(
    [["/ask", "/help"]],
    resize_keyboard=True,
    one_time_keyboard=False,
)

# ===== Обработчики команд =====
START, GET_NAME1 = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text ( "Привет! Я бот для рекомендательных систем.", reply_markup=main_keyboard )
    api_check_user = f"https://swpdb-production.up.railway.app/users/{update.effective_user.id}"
   
    async with httpx.AsyncClient() as client:
        try:
            response_get_user = await client.get(api_check_user)
            print("вот твой код на повторный запрос", response_get_user.status_code)
            if response_get_user.status_code == 200:
                await update.message.reply_text( "Вы уже зарегистрированы!", reply_markup=main_keyboard )
                return ConversationHandler.END
                
        except httpx.RequestError as e:
            await update.message.reply_text( "Ошибка при запросе на сервере. Обратитесь к администратору", reply_markup=main_keyboard )
            return ConversationHandler.END
    await update.message.reply_text( "Пожалуйста, введите ваше имя: ", reply_markup=main_keyboard )
    return GET_NAME1


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    """Получение и сохранение имени пользователя"""
    user_name = update.message.text
    context.user_data['name'] = user_name  # Сохраняем имя

    payload_name_json = {
        "_id" : update.effective_user.id,
        "name" : user_name,
    }
    
    api_create_user = "https://swpdb-production.up.railway.app/users/"
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(api_create_user, json=payload_name_json)
            await update.message.reply_text( f"Отлично, {user_name}! Теперь вы можете пользоваться ботом.", reply_markup=main_keyboard )
        except httpx.RequestError as e:
            await update.message.reply_text( "Ошибка при запросе на сервере. Обратитесь к администратору", reply_markup=main_keyboard )
    return ConversationHandler.END
    

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена ввода имени"""
    await update.message.reply_text( "Отмена", reply_markup=main_keyboard )
    if 'conv_id' in context.user_data:
        del context.user_data['conv_id']
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Доступные команды:\n/ask - задать вопрос\n/help - помощь",
        reply_markup=main_keyboard,
    )

WAITING_FOR_MESSAGE = 1
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ask_keyboard = ReplyKeyboardMarkup([["Отмена"]], resize_keyboard=True, one_time_keyboard=True)
    context.user_data['last_message'] = None
    await update.message.reply_text("Напишите запрос:", reply_markup=main_keyboard)
    async with httpx.AsyncClient() as client:
        api_create_conv = "https://swpdb-production.up.railway.app/conversations/"
        payload_conv_json = {
            "user_id": update.effective_user.id,
            "messages": []
        }
        try:
            response_create_conv = await client.post(api_create_conv, json=payload_conv_json)
            context.user_data['conv_id'] = response_create_conv.json().get("_id")
        except httpx.RequestError as e:
            await update.message.reply_text(
                "Ошибка на сервере -> обратитесь к админинстратору",
                reply_markup=main_keyboard,
            )
        return WAITING_FOR_MESSAGE
async def ask_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_text = update.message.text
    context.user_data['last_message'] = user_text
    await update.message.reply_text(
        f"ваш текст: {user_text}",
        reply_markup=main_keyboard,
    )
    api_add_message = f"https://swpdb-production.up.railway.app/conversations/{context.user_data['conv_id']}/messages"
    payload_add_message = {
        "sender" : "user",
        "text" : user_text,
        "time" : update.message.date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    }
    async with httpx.AsyncClient() as client:
        try:
            response_add_message = await client.post(api_add_message, json=payload_add_message)
        except httpx.RequestError as e:
            await update.message.reply_text(
                "Обратитесь к администратору(((", 
                reply_markup=main_keyboard,
            )
    return WAITING_FOR_MESSAGE
# ===== Регистрация обработчиков =====
def register_handlers():
    conv_handler_start = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_NAME1:[
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_name,
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler_start)
    application.add_handler(CommandHandler("help", help_command))

    ask_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("ask", ask)],
        states={
            WAITING_FOR_MESSAGE: [
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
    application.add_handler(ask_conv_handler)


register_handlers()

# ===== Вебхук и запуск =====
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
async def health_check():
    return {"status": "Bot is running"}

@app.on_event("startup")
async def startup():
    await application.initialize()
    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")

@app.on_event("shutdown")
async def shutdown():
    await application.bot.delete_webhook()
    await application.shutdown()

# Запуск сервера (важно для Railway)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Railway использует $PORT
    uvicorn.run(app, host="0.0.0.0", port=port)
