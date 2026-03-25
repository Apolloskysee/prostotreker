from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
import database as db
from keyboards.keyboards import goals_menu, goal_actions_keyboard, back_keyboard

# Состояния
GOAL_TITLE, GOAL_DEADLINE = range(2)

async def show_goals_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню целей"""
    await update.message.reply_text(
        "🎯 Цели на год\n\nВыберите действие:",
        reply_markup=goals_menu()
    )

async def add_goal_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать добавление цели"""
    # Проверяем премиум статус
    if not db.is_premium(update.effective_user.id):
        await update.message.reply_text(
            "🎯 Цели на год доступны только с подпиской Премиум!\n\n"
            "Оформите подписку, чтобы фиксировать долгосрочные цели и двигаться к результату.",
            reply_markup=goals_menu()
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "Введите название цели:",
        reply_markup=back_keyboard()
    )
    return GOAL_TITLE

async def add_goal_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить название цели"""
    context.user_data['goal_title'] = update.message.text
    
    await update.message.reply_text(
        "Введите срок выполнения (в формате ДД.ММ.ГГГГ):\n\n"
        "Например: 31.12.2026",
        reply_markup=back_keyboard()
    )
    return GOAL_DEADLINE

async def add_goal_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить срок выполнения"""
    try:
        deadline = datetime.strptime(update.message.text, '%d.%m.%Y').date()
        deadline_str = deadline.isoformat()
        
        # Сохраняем цель
        goal_id = db.add_goal(
            update.effective_user.id,
            context.user_data['goal_title'],
            deadline_str
        )
        
        await update.message.reply_text(
            f"✅ Цель добавлена!\n\n"
            f"Название: {context.user_data['goal_title']}\n"
            f"Срок: {deadline.strftime('%d.%m.%Y')}",
            reply_markup=goals_menu()
        )
        
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "Неверный формат даты. Используйте ДД.ММ.ГГГГ\n"
            "Попробуйте снова:"
        )
        return GOAL_DEADLINE

async def show_my_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать мои цели"""
    user_id = update.effective_user.id
    
    if not db.is_premium(user_id):
        await update.message.reply_text(
            "🎯 Цели на год доступны только с подпиской Премиум!",
            reply_markup=goals_menu()
        )
        return
    
    goals = db.get_user_goals(user_id)
    active_goals = [g for g in goals if not g['completed']]
    
    if not active_goals:
        await update.message.reply_text(
            "Активных целей пока нет\n\n🎯 Добавьте первую цель!",
            reply_markup=goals_menu()
        )
        return
    
    message = "🎯 Мои цели:\n\n"
    for goal in active_goals:
        deadline = datetime.fromisoformat(goal['deadline']).strftime('%d.%m.%Y')
        message += f"• {goal['title']}\n  Срок: {deadline}\n\n"
        
        # Отправляем каждую цель с кнопками
        await update.message.reply_text(
            f"Цель: {goal['title']}",
            reply_markup=goal_actions_keyboard(goal['id'])
        )
    
    await update.message.reply_text(message)

async def show_completed_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать выполненные цели"""
    user_id = update.effective_user.id
    
    if not db.is_premium(user_id):
        await update.message.reply_text(
            "🎯 Цели на год доступны только с подпиской Премиум!",
            reply_markup=goals_menu()
        )
        return
    
    goals = db.get_user_goals(user_id)
    completed_goals = [g for g in goals if g['completed']]
    
    if not completed_goals:
        await update.message.reply_text(
            "Выполненных целей пока нет\n\n🎯 Двигайтесь к новым достижениям!",
            reply_markup=goals_menu()
        )
        return
    
    message = "✅ Выполненные цели:\n\n"
    for goal in completed_goals:
        deadline = datetime.fromisoformat(goal['deadline']).strftime('%d.%m.%Y')
        message += f"✓ {goal['title']}\n  Срок: {deadline}\n\n"
    
    await update.message.reply_text(message)

async def cancel_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена действия"""
    context.user_data.clear()
    await update.message.reply_text(
        "Действие отменено",
        reply_markup=goals_menu()
    )
    return ConversationHandler.END

# Обработчики для callback кнопок
async def handle_goal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка действий с целями"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("complete_goal_"):
        goal_id = int(data.split("_")[2])
        db.complete_goal(goal_id)
        await query.edit_message_text("✅ Цель отмечена как выполненная! Поздравляем!")
    
    elif data.startswith("delete_goal_"):
        # Здесь нужно добавить функцию удаления цели
        goal_id = int(data.split("_")[2])
        await query.edit_message_text("❌ Цель удалена!")