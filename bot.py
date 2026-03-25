import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ConversationHandler
)

from config import TOKEN
import database as db
from handlers import tasks, habits, goals, analytics, premium, settings
from utils.reminders import start_reminder_scheduler
from keyboards.keyboards import main_menu

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
db.init_db()

async def start(update: Update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    db.create_user(
        user.id,
        user.username,
        user.first_name,
        user.last_name
    )
    await update.message.reply_text(
        f"Добро пожаловать, {user.first_name}! 👋\n\n"
        f"Просто Трекер помогает сохранять дисциплину "
        f"и двигаться к целям каждый день.\n\n"
        f"Используйте меню для навигации:",
        reply_markup=main_menu()
    )

async def handle_message(update: Update, context):
    """Обработчик текстовых сообщений"""
    text = update.message.text
    
    if text == "📋 Задачи":
        await tasks.show_tasks_menu(update, context)
    elif text == "🔄 Привычки":
        await habits.show_habits_menu(update, context)
    elif text == "🎯 Цели на год":
        await goals.show_goals_menu(update, context)
    elif text == "📊 Аналитика":
        await analytics.show_analytics(update, context)
    elif text == "⚙️ Настройки":
        await settings.show_settings(update, context)
    elif text == "💎 Премиум":
        await premium.show_premium(update, context)
    elif text == "➕ Добавить задачу":
        await tasks.add_task_start(update, context)
    elif text == "📅 Задачи на сегодня":
        await tasks.show_today_tasks(update, context)
    elif text == "⭐ Важные задачи":
        await tasks.show_important_tasks(update, context)
    elif text == "➕ Добавить привычку":
        await habits.add_habit_start(update, context)
    elif text == "📊 Мои привычки":
        await habits.show_my_habits(update, context)
    elif text == "✅ Отметить выполнение":
        await habits.complete_habit_today(update, context)
    elif text == "➕ Добавить цель":
        await goals.add_goal_start(update, context)
    elif text == "🎯 Мои цели":
        await goals.show_my_goals(update, context)
    elif text == "✅ Выполненные цели":
        await goals.show_completed_goals(update, context)
    elif text == "👤 Профиль":
        await settings.show_profile(update, context)
    elif text == "💎 Подписка":
        await settings.show_subscription(update, context)
    elif text == "🔔 Уведомления":
        await update.message.reply_text("🔔 Настройки уведомлений будут доступны в следующем обновлении!")
    elif text == "⚙️ Предпочтения":
        await update.message.reply_text("⚙️ Настройки предпочтений будут доступны в следующем обновлении!")
    elif text == "❓ Помощь":
        await settings.show_help(update, context)
    elif text == "◀️ Назад":
        await update.message.reply_text("Главное меню", reply_markup=main_menu())
    elif context.user_data.get('selecting_habit'):
        await habits.handle_habit_selection(update, context)

async def post_init(application: Application):
    """Выполняется после инициализации приложения, до запуска polling."""
    await start_reminder_scheduler(application)

def main():
    """Запуск бота с явным созданием event loop для Python 3.14+"""
    # Создаём и устанавливаем event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    application = Application.builder().token(TOKEN).post_init(post_init).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    
    # ConversationHandler для задач
    task_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^➕ Добавить задачу$'), tasks.add_task_start)],
        states={
            tasks.TASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tasks.add_task_title)],
            tasks.TASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tasks.add_task_date)],
            tasks.TASK_REMINDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, tasks.add_task_reminder)],
            tasks.TASK_IMPORTANT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tasks.add_task_important)],
        },
        fallbacks=[CommandHandler("cancel", tasks.cancel)],
    )
    application.add_handler(task_conv)
    
    # ConversationHandler для привычек
    habit_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^➕ Добавить привычку$'), habits.add_habit_start)],
        states={
            habits.HABIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, habits.add_habit_name)],
            habits.HABIT_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, habits.add_habit_days)],
            habits.HABIT_REMINDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, habits.add_habit_reminder)],
        },
        fallbacks=[CommandHandler("cancel", habits.cancel_habit)],
    )
    application.add_handler(habit_conv)
    
    # ConversationHandler для целей
    goal_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^➕ Добавить цель$'), goals.add_goal_start)],
        states={
            goals.GOAL_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, goals.add_goal_title)],
            goals.GOAL_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, goals.add_goal_deadline)],
        },
        fallbacks=[CommandHandler("cancel", goals.cancel_goal)],
    )
    application.add_handler(goal_conv)
    
    # Callback-обработчики
    application.add_handler(CallbackQueryHandler(tasks.handle_task_callback, pattern='^(complete|delete)_task_'))
    application.add_handler(CallbackQueryHandler(habits.handle_habit_callback, pattern='^(complete|delete)_habit_'))
    application.add_handler(CallbackQueryHandler(goals.handle_goal_callback, pattern='^(complete|delete)_goal_'))
    application.add_handler(CallbackQueryHandler(premium.handle_premium_callback, pattern='^premium_'))
    application.add_handler(CallbackQueryHandler(premium.handle_premium_callback, pattern='^back_to_menu$'))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Бот запущен...")
    # Запускаем polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()