from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime, timedelta
import database as db
from keyboards.keyboards import tasks_menu, task_actions_keyboard, main_menu, back_keyboard

# Состояния для ConversationHandler
TASK_TITLE, TASK_DATE, TASK_REMINDER, TASK_IMPORTANT = range(4)

async def show_tasks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню задач"""
    await update.message.reply_text(
        "📋 Управление задачами\n\nВыберите действие:",
        reply_markup=tasks_menu()
    )

async def add_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать добавление задачи"""
    await update.message.reply_text(
        "Введите название задачи:",
        reply_markup=back_keyboard()
    )
    return TASK_TITLE

async def add_task_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить название задачи"""
    context.user_data['task_title'] = update.message.text
    
    await update.message.reply_text(
        "Выберите дату выполнения (в формате ДД.ММ.ГГГГ):\n\n"
        "Или отправьте 'сегодня' или 'завтра':",
        reply_markup=back_keyboard()
    )
    return TASK_DATE

async def add_task_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить дату задачи"""
    date_text = update.message.text.lower()
    
    if date_text == 'сегодня':
        task_date = datetime.now().date()
    elif date_text == 'завтра':
        task_date = datetime.now().date() + timedelta(days=1)
    else:
        try:
            task_date = datetime.strptime(date_text, '%d.%m.%Y').date()
        except:
            await update.message.reply_text(
                "Неверный формат даты. Используйте ДД.ММ.ГГГГ\n"
                "Или отправьте 'сегодня' или 'завтра':"
            )
            return TASK_DATE
    
    context.user_data['task_date'] = task_date.isoformat()
    
    await update.message.reply_text(
        "Хотите установить напоминание?\n"
        "Отправьте время в формате ЧЧ:ММ (например, 14:30)\n"
        "Или отправьте 'нет', чтобы пропустить:"
    )
    return TASK_REMINDER

async def add_task_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить время напоминания"""
    reminder_text = update.message.text.lower()
    
    if reminder_text != 'нет':
        try:
            reminder_time = reminder_text
            context.user_data['task_reminder'] = reminder_time
        except:
            await update.message.reply_text(
                "Неверный формат времени. Используйте ЧЧ:ММ\n"
                "Или отправьте 'нет', чтобы пропустить:"
            )
            return TASK_REMINDER
    else:
        context.user_data['task_reminder'] = None
    
    keyboard = ReplyKeyboardMarkup(
        [["Да", "Нет"]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await update.message.reply_text(
        "Отметить как важную задачу?",
        reply_markup=keyboard
    )
    return TASK_IMPORTANT

async def add_task_important(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить статус важности задачи"""
    important = 1 if update.message.text.lower() == 'да' else 0
    
    # Сохраняем задачу в базу данных
    task_id = db.add_task(
        update.effective_user.id,
        context.user_data['task_title'],
        context.user_data['task_date'],
        context.user_data.get('task_reminder'),
        important
    )
    
    await update.message.reply_text(
        f"✅ Задача добавлена!\n\n"
        f"Название: {context.user_data['task_title']}\n"
        f"Дата: {context.user_data['task_date']}\n"
        f"Важная: {'Да' if important else 'Нет'}",
        reply_markup=tasks_menu()
    )
    
    # Очищаем данные пользователя
    context.user_data.clear()
    return ConversationHandler.END

async def show_today_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать задачи на сегодня"""
    today = datetime.now().date().isoformat()
    tasks = db.get_tasks_for_date(update.effective_user.id, today)
    
    if not tasks:
        await update.message.reply_text(
            "📭 На сегодня задач нет",
            reply_markup=tasks_menu()
        )
        return
    
    message = "📅 Задачи на сегодня:\n\n"
    for task in tasks:
        status = "✅" if task['completed'] else "⭕️"
        important = "⭐️ " if task['important'] else ""
        message += f"{status} {important}{task['title']}\n"
        
        # Отправляем каждую задачу с кнопками действий
        if not task['completed']:
            await update.message.reply_text(
                f"Задача: {task['title']}",
                reply_markup=task_actions_keyboard(task['id'])
            )
    
    if message != "📅 Задачи на сегодня:\n\n":
        await update.message.reply_text(message)

async def show_important_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать важные задачи"""
    user_id = update.effective_user.id
    
    # Проверяем премиум статус
    if not db.is_premium(user_id):
        await update.message.reply_text(
            "⭐️ Функция 'Важные задачи' доступна только с подпиской Премиум!\n\n"
            "Оформите подписку, чтобы отмечать важные задачи и не терять приоритеты.",
            reply_markup=main_menu()
        )
        return
    
    # Здесь нужно добавить запрос к базе данных для важных задач
    await update.message.reply_text(
        "⭐️ Важные задачи\n\n"
        "Функция в разработке. Скоро здесь появятся все важные задачи!",
        reply_markup=tasks_menu()
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена действия"""
    context.user_data.clear()
    await update.message.reply_text(
        "Действие отменено",
        reply_markup=tasks_menu()
    )
    return ConversationHandler.END

# Обработчики для callback кнопок
async def handle_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка действий с задачами"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data.startswith("complete_task_"):
        task_id = int(data.split("_")[2])
        db.complete_task(task_id)
        await query.edit_message_text("✅ Задача отмечена как выполненная!")
    
    elif data.startswith("delete_task_"):
        task_id = int(data.split("_")[2])
        db.delete_task(task_id)
        await query.edit_message_text("❌ Задача удалена!")