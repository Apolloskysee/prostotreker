from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime, timedelta
import json
import database as db
from keyboards.keyboards import habits_menu, habit_actions_keyboard, back_keyboard

# Состояния
HABIT_NAME, HABIT_DAYS, HABIT_REMINDER = range(3)

async def show_habits_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню привычек"""
    await update.message.reply_text(
        "🔄 Управление привычками\n\nВыберите действие:",
        reply_markup=habits_menu()
    )

async def add_habit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать добавление привычки"""
    # Проверяем премиум статус
    if not db.is_premium(update.effective_user.id):
        await update.message.reply_text(
            "🔄 Функция 'Привычки' доступна только с подпиской Премиум!\n\n"
            "Оформите подписку, чтобы отслеживать привычки без ограничений.",
            reply_markup=habits_menu()
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "Введите название привычки:",
        reply_markup=back_keyboard()
    )
    return HABIT_NAME

async def add_habit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить название привычки"""
    context.user_data['habit_name'] = update.message.text
    
    days_keyboard = ReplyKeyboardMarkup(
        [
            ["ПН", "ВТ", "СР", "ЧТ", "ПТ"],
            ["СБ", "ВС", "Все дни", "Будни"],
            ["◀️ Назад"]
        ],
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "Выберите дни для выполнения привычки:",
        reply_markup=days_keyboard
    )
    return HABIT_DAYS

async def add_habit_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить дни привычки"""
    days_text = update.message.text
    
    days_mapping = {
        "ПН": "Mon", "ВТ": "Tue", "СР": "Wed", "ЧТ": "Thu",
        "ПТ": "Fri", "СБ": "Sat", "ВС": "Sun",
        "Все дни": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "Будни": ["Mon", "Tue", "Wed", "Thu", "Fri"]
    }
    
    if days_text in days_mapping:
        if isinstance(days_mapping[days_text], list):
            days = days_mapping[days_text]
        else:
            days = [days_mapping[days_text]]
        context.user_data['habit_days'] = days
    else:
        await update.message.reply_text(
            "Пожалуйста, выберите дни из предложенных вариантов:"
        )
        return HABIT_DAYS
    
    await update.message.reply_text(
        "Хотите установить напоминание?\n"
        "Отправьте время в формате ЧЧ:ММ (например, 09:00)\n"
        "Или отправьте 'нет', чтобы пропустить:",
        reply_markup=back_keyboard()
    )
    return HABIT_REMINDER

async def add_habit_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить время напоминания"""
    reminder_text = update.message.text.lower()
    
    if reminder_text != 'нет':
        context.user_data['habit_reminder'] = reminder_text
    else:
        context.user_data['habit_reminder'] = None
    
    # Сохраняем привычку
    habit_id = db.add_habit(
        update.effective_user.id,
        context.user_data['habit_name'],
        context.user_data['habit_days'],
        context.user_data.get('habit_reminder')
    )
    
    days_str = ", ".join(context.user_data['habit_days'])
    
    await update.message.reply_text(
        f"✅ Привычка добавлена!\n\n"
        f"Название: {context.user_data['habit_name']}\n"
        f"Дни: {days_str}\n"
        f"Напоминание: {context.user_data.get('habit_reminder', 'Не установлено')}",
        reply_markup=habits_menu()
    )
    
    context.user_data.clear()
    return ConversationHandler.END

async def show_my_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать мои привычки"""
    user_id = update.effective_user.id
    
    if not db.is_premium(user_id):
        await update.message.reply_text(
            "🔄 Привычки доступны только с подпиской Премиум!",
            reply_markup=habits_menu()
        )
        return
    
    habits = db.get_user_habits(user_id)
    
    if not habits:
        await update.message.reply_text(
            "Привычек пока что нет\n\n➕ Добавьте первую привычку!",
            reply_markup=habits_menu()
        )
        return
    
    message = "📊 Мои привычки:\n\n"
    for habit in habits:
        days = json.loads(habit['days'])
        days_str = ", ".join(days)
        message += f"• {habit['name']}\n  Дни: {days_str}\n\n"
        
        # Отправляем каждую привычку с кнопками
        await update.message.reply_text(
            f"Привычка: {habit['name']}",
            reply_markup=habit_actions_keyboard(habit['id'])
        )
    
    await update.message.reply_text(message)

async def complete_habit_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отметить выполнение привычки"""
    user_id = update.effective_user.id
    
    if not db.is_premium(user_id):
        await update.message.reply_text(
            "✅ Отметка выполнения привычек доступна только с подпиской Премиум!",
            reply_markup=habits_menu()
        )
        return
    
    habits = db.get_user_habits(user_id)
    
    if not habits:
        await update.message.reply_text(
            "У вас пока нет привычек. Добавьте привычку, чтобы начать!",
            reply_markup=habits_menu()
        )
        return
    
    keyboard = []
    for habit in habits:
        keyboard.append([f"✅ {habit['name']}"])
    keyboard.append(["◀️ Назад"])
    
    await update.message.reply_text(
        "Выберите привычку для отметки выполнения:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    context.user_data['selecting_habit'] = True

async def handle_habit_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора привычки для выполнения"""
    if not context.user_data.get('selecting_habit'):
        return
    
    habit_name = update.message.text.replace("✅ ", "")
    today = datetime.now().date().isoformat()
    
    # Находим привычку
    habits = db.get_user_habits(update.effective_user.id)
    habit = next((h for h in habits if h['name'] == habit_name), None)
    
    if habit:
        db.complete_habit(habit['id'], today)
        await update.message.reply_text(
            f"✅ Отлично! Вы выполнили привычку '{habit_name}'!",
            reply_markup=habits_menu()
        )
    else:
        await update.message.reply_text(
            "Привычка не найдена",
            reply_markup=habits_menu()
        )
    
    context.user_data['selecting_habit'] = False
async def handle_habit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка действий с привычками (выполнено/удалить)"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("complete_habit_"):
        habit_id = int(data.split("_")[2])
        today = datetime.now().date().isoformat()
        db.complete_habit(habit_id, today)
        await query.edit_message_text("✅ Привычка отмечена как выполненная!")
    
    elif data.startswith("delete_habit_"):
        habit_id = int(data.split("_")[2])
        # Удаляем привычку
        with db.get_db_connection() as conn:
            conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
            conn.execute("DELETE FROM habit_completions WHERE habit_id = ?", (habit_id,))
            conn.commit()
        await query.edit_message_text("❌ Привычка удалена!")


async def cancel_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена действия"""
    context.user_data.clear()
    await update.message.reply_text(
        "Действие отменено",
        reply_markup=habits_menu()
    )
    return ConversationHandler.END

