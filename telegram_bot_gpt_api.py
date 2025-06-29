import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from gpt_api_client import GPTAPIClient

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_TOKEN', '7732002021:AAE2Bm08v2RoxRDsvyAy7HyjfREr05VenhQ')

class GPTTelegramBot:
    def __init__(self):
        self.api_client = GPTAPIClient()
        self.conversation_history = {}
        self.system_prompt = self.load_enhanced_system_prompt()
    def load_enhanced_system_prompt(self):
        try:
            if os.path.exists('enhanced_system_prompt.txt'):
                with open('enhanced_system_prompt.txt', 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception as e:
            logger.warning(f"Could not load enhanced system prompt: {e}")
        return """Ты - эксперт по приложению NamazApp. Твоя задача - давать точные, полезные и дружелюбные ответы на вопросы пользователей о приложении для молитв.

Важные принципы:
1. Всегда отвечай на русском языке
2. Используй Markdown форматирование для ссылок и выделения
3. Будь точным и информативным
4. Если не знаешь ответа, направь пользователя в службу поддержки
5. Используй информацию из приложения NamazApp
6. Отвечай кратко, но информативно
7. Всегда будь полезным и дружелюбным

Ты обучен на большом количестве примеров вопросов и ответов о приложении NamazApp."""
    async def start(self, update: Update, context):
        user = update.effective_user
        welcome_message = f"""Ассаляму алейкум, {user.first_name}! 👋

Я - помощник приложения NamazApp. Могу ответить на ваши вопросы о:
• Настройках приложения
• Молитвах и их правилах
• Функциях приложения
• Рекомендациях по изучению

Просто задайте мне любой вопрос! 📱

Команды:
/help - показать справку
/status - проверить статус бота"""
        await update.message.reply_text(welcome_message)
        self.conversation_history[user.id] = []
    async def help_command(self, update: Update, context):
        help_text = """🤖 **Помощь по использованию бота**

**Как использовать:**
• Просто напишите ваш вопрос о приложении NamazApp
• Я отвечу на русском языке с полезной информацией
• Использую Markdown для лучшего форматирования

**Примеры вопросов:**
• "Как изменить язык приложения?"
• "Рекомендуйте приложения для изучения арабского"
• "Как настроить время молитв?"
• "Где найти настройки молитв?"

**Команды:**
/start - начать работу с ботом
/help - показать эту справку
/status - проверить статус бота

**Если у вас есть сложный вопрос:**
Обратитесь в службу поддержки через WhatsApp в приложении."""
        await update.message.reply_text(help_text, parse_mode='Markdown')
    async def status_command(self, update: Update, context):
        api_status = "✅ Работает" if self.api_client.test_connection() else "❌ Недоступен"
        status_text = f"""📊 **Статус бота**

**API GPT:** {api_status}
**Системный промпт:** ✅ Загружен
**История диалогов:** {len(self.conversation_history)} пользователей

**Последние обновления:**
• Интеграция с GPT API
• Улучшенные ответы на русском языке
• Поддержка Markdown форматирования
• История диалогов для контекста"""
        await update.message.reply_text(status_text, parse_mode='Markdown')
    async def handle_message(self, update: Update, context):
        user = update.effective_user
        user_message = update.message.text
        if user.id not in self.conversation_history:
            self.conversation_history[user.id] = []
        self.conversation_history[user.id].append({
            'role': 'user',
            'content': user_message
        })
        if len(self.conversation_history[user.id]) > 10:
            self.conversation_history[user.id] = self.conversation_history[user.id][-10:]
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        try:
            response = self.api_client.generate_response(
                user_message=user_message,
                system_message=self.system_prompt
            )
            self.conversation_history[user.id].append({
                'role': 'assistant',
                'content': response
            })
            keyboard = [
                [
                    InlineKeyboardButton("👍 Полезно", callback_data=f"feedback_good_{user.id}"),
                    InlineKeyboardButton("👎 Не полезно", callback_data=f"feedback_bad_{user.id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                response,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            error_message = """Извините, произошла ошибка при генерации ответа. 

Попробуйте:
• Переформулировать вопрос
• Обратиться в службу поддержки через WhatsApp
• Использовать команду /status для проверки

Ошибка: """ + str(e)
            await update.message.reply_text(error_message)
    async def handle_feedback(self, update: Update, context):
        query = update.callback_query
        await query.answer()
        feedback_data = query.data.split('_')
        feedback_type = feedback_data[1]
        user_id = feedback_data[2]
        logger.info(f"User {user_id} gave {feedback_type} feedback")
        if feedback_type == 'good':
            await query.edit_message_text(
                query.message.text + "\n\n✅ Спасибо за положительный отзыв!"
            )
        else:
            await query.edit_message_text(
                query.message.text + "\n\n❌ Спасибо за обратную связь! Мы постараемся улучшить ответы."
            )
def main():
    bot = GPTTelegramBot()
    application = Application.builder().token(TOKEN).build()
    commands = [
        BotCommand("start", "Начать работу с ботом"),
        BotCommand("help", "Справка по использованию"),
        BotCommand("status", "Показать статус бота"),
        BotCommand("ask", "Задать вопрос о NamazApp")
    ]
    async def set_commands(app):
        await app.bot.set_my_commands(commands)
    async def start_wrapper(update: Update, context):
        return await bot.start(update, context)
    async def help_wrapper(update: Update, context):
        return await bot.help_command(update, context)
    async def status_wrapper(update: Update, context):
        return await bot.status_command(update, context)
    async def message_wrapper(update: Update, context):
        return await bot.handle_message(update, context)
    async def feedback_wrapper(update: Update, context):
        return await bot.handle_feedback(update, context)
    application.add_handler(CommandHandler("start", start_wrapper))
    application.add_handler(CommandHandler("help", help_wrapper))
    application.add_handler(CommandHandler("status", status_wrapper))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_wrapper))
    application.add_handler(CallbackQueryHandler(feedback_wrapper))
    logger.info("Starting GPT API Telegram Bot...")
    application.post_init = set_commands
    application.run_polling()
if __name__ == '__main__':
    main() 