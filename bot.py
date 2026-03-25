import asyncio
import json
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ConversationHandler
)

from config import TOKEN
import database as db
from handlers import tasks, habits, goals, analytics, premium, settings, finance
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
    elif text == "💰 Финансы":
        await finance.show_finance_menu(update, context)
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
    
    # Финансовые команды из меню
    elif text == "💰 Добавить трату" or text == "💵 Добавить доход":
        await finance.add_transaction_start(update, context)
    elif text == "📊 Аналитика" and context.user_data.get('in_finance'):
        await finance.show_budget_analysis(update, context)
    elif text == "📜 История" and context.user_data.get('in_finance'):
        await finance.show_transactions(update, context)
    elif text == "👥 Совместный бюджет" and context.user_data.get('in_finance'):
        await finance.create_shared_account(update, context)
    elif text == "💳 Долги" and context.user_data.get('in_finance'):
        await finance.show_debts(update, context)

async def webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка данных из мини-приложения"""
    data = update.effective_message.web_app_data.data
    try:
        payload = json.loads(data)
        command = payload.get('command')
        message_id = payload.get('message_id')
        user_id = update.effective_user.id

        # Задачи
        if command == 'get_tasks':
            today = datetime.now().date().isoformat()
            tasks = db.get_tasks_for_date(user_id, today)
            tasks_list = [dict(task) for task in tasks]
            await update.message.reply_text(json.dumps({
                'message_id': message_id,
                'tasks': tasks_list
            }))

        elif command == 'complete_task':
            task_id = payload['task_id']
            db.complete_task(task_id)
            await update.message.reply_text(json.dumps({
                'message_id': message_id,
                'status': 'ok'
            }))

        elif command == 'delete_task':
            task_id = payload['task_id']
            db.delete_task(task_id)
            await update.message.reply_text(json.dumps({
                'message_id': message_id,
                'status': 'ok'
            }))

        elif command == 'add_task':
            title = payload['title']
            date_str = payload.get('date')
            if date_str:
                try:
                    date = datetime.strptime(date_str, '%d.%m.%Y').date().isoformat()
                except:
                    date = datetime.now().date().isoformat()
            else:
                date = datetime.now().date().isoformat()
            db.add_task(user_id, title, date)
            await update.message.reply_text(json.dumps({
                'message_id': message_id,
                'status': 'ok'
            }))

        # Привычки
        elif command == 'get_habits':
            habits = db.get_user_habits(user_id)
            habits_list = [dict(habit) for habit in habits]
            await update.message.reply_text(json.dumps({
                'message_id': message_id,
                'habits': habits_list
            }))

        elif command == 'complete_habit':
            habit_id = payload['habit_id']
            today = datetime.now().date().isoformat()
            db.complete_habit(habit_id, today)
            await update.message.reply_text(json.dumps({
                'message_id': message_id,
                'status': 'ok'
            }))

        elif command == 'delete_habit':
            habit_id = payload['habit_id']
            if hasattr(db, 'delete_habit'):
                db.delete_habit(habit_id)
            else:
                with db.get_db_connection() as conn:
                    conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
                    conn.execute("DELETE FROM habit_completions WHERE habit_id = ?", (habit_id,))
                    conn.commit()
            await update.message.reply_text(json.dumps({
                'message_id': message_id,
                'status': 'ok'
            }))

        elif command == 'add_habit':
            name = payload['name']
            days = payload.get('days', [])
            db.add_habit(user_id, name, days, None)
            await update.message.reply_text(json.dumps({
                'message_id': message_id,
                'status': 'ok'
            }))

        # Цели
        elif command == 'get_goals':
            goals = db.get_user_goals(user_id)
            goals_list = [dict(goal) for goal in goals]
            await update.message.reply_text(json.dumps({
                'message_id': message_id,
                'goals': goals_list
            }))

        elif command == 'complete_goal':
            goal_id = payload['goal_id']
            db.complete_goal(goal_id)
            await update.message.reply_text(json.dumps({
                'message_id': message_id,
                'status': 'ok'
            }))

        elif command == 'delete_goal':
            goal_id = payload['goal_id']
            with db.get_db_connection() as conn:
                conn.execute("DELETE FROM yearly_goals WHERE id = ?", (goal_id,))
                conn.commit()
            await update.message.reply_text(json.dumps({
                'message_id': message_id,
                'status': 'ok'
            }))

        elif command == 'add_goal':
            title = payload['title']
            deadline_str = payload.get('deadline')
            if deadline_str:
                try:
                    deadline = datetime.strptime(deadline_str, '%d.%m.%Y').date().isoformat()
                except:
                    deadline = datetime.now().date().isoformat()
            else:
                deadline = datetime.now().date().isoformat()
            db.add_goal(user_id, title, deadline)
            await update.message.reply_text(json.dumps({
                'message_id': message_id,
                'status': 'ok'
            }))

        # Финансы
        elif command == 'get_finance':
            if hasattr(db, 'get_finance_stats'):
                stats = db.get_finance_stats(user_id)
                transactions = db.get_transactions(user_id, limit=20)
                await update.message.reply_text(json.dumps({
                    'message_id': message_id,
                    'stats': stats,
                    'transactions': [dict(t) for t in transactions]
                }))
            else:
                await update.message.reply_text(json.dumps({
                    'message_id': message_id,
                    'stats': {'balance': 0, 'income': 0, 'expense': 0},
                    'transactions': []
                }))

        elif command == 'add_transaction':
            amount = float(payload.get('amount', 0))
            trans_type = payload.get('type')
            category = payload.get('category')
            description = payload.get('description')
            db.add_transaction(user_id, amount, trans_type, category, description)
            await update.message.reply_text(json.dumps({
                'message_id': message_id,
                'status': 'ok'
            }))

        else:
            await update.message.reply_text(json.dumps({
                'message_id': message_id,
                'error': 'unknown command'
            }))

    except Exception as e:
        await update.message.reply_text(json.dumps({
            'error': str(e)
        }))

async def post_init(application: Application):
    """Выполняется после инициализации приложения, до запуска polling."""
    await start_reminder_scheduler(application)

def main():
    """Запуск бота с явным созданием event loop для Python 3.14+"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # Команды
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

    # ConversationHandler для финансов
    finance_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^(💰 Добавить трату|💵 Добавить доход)$'), finance.add_transaction_start)
        ],
        states={
            finance.ADD_TRANSACTION_TYPE: [CallbackQueryHandler(finance.add_transaction_type, pattern='^type_')],
            finance.ADD_TRANSACTION_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, finance.add_transaction_amount)],
            finance.ADD_TRANSACTION_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, finance.add_transaction_category)],
            finance.ADD_TRANSACTION_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, finance.add_transaction_desc)],
            finance.SELECT_DEBT_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, finance.add_shared_partner)],
        },
        fallbacks=[CommandHandler("cancel", finance.cancel_finance)],
    )
    application.add_handler(finance_conv)

    # Callback-обработчики (для inline кнопок)
    application.add_handler(CallbackQueryHandler(tasks.handle_task_callback, pattern='^(complete|delete)_task_'))
    application.add_handler(CallbackQueryHandler(habits.handle_habit_callback, pattern='^(complete|delete)_habit_'))
    application.add_handler(CallbackQueryHandler(goals.handle_goal_callback, pattern='^(complete|delete)_goal_'))
    application.add_handler(CallbackQueryHandler(premium.handle_premium_callback, pattern='^premium_'))
    application.add_handler(CallbackQueryHandler(premium.handle_premium_callback, pattern='^back_to_menu$'))
    application.add_handler(CallbackQueryHandler(finance.handle_finance_callback, pattern='^(type_|cancel)'))

    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Обработчик данных из мини-приложения (WebApp)
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data))

    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()