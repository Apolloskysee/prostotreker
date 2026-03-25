from telegram import Update
from telegram.ext import ContextTypes
import database as db
from keyboards.keyboards import settings_menu, main_menu

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать настройки"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    message = (
        "⚙️ **Основные настройки**\n\n"
        f"👤 Профиль: @{user['username'] or user['first_name']}\n"
        f"💎 Подписка: {'Активна' if db.is_premium(user_id) else 'Неактивна'}\n"
        "🔔 Уведомления: Вкл\n"
        "⚙️ Предпочтения: По умолчанию"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=settings_menu())

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать профиль"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    message = (
        "👤 **Ваш профиль**\n\n"
        f"Имя: {user['first_name'] or 'Не указано'}\n"
        f"Фамилия: {user['last_name'] or 'Не указана'}\n"
        f"Username: @{user['username'] or 'Не указан'}\n"
        f"ID: {user_id}\n\n"
        f"💎 Статус: {'Премиум' if db.is_premium(user_id) else 'Бесплатный'}"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=settings_menu())

async def show_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о подписке"""
    user_id = update.effective_user.id
    is_premium = db.is_premium(user_id)
    
    if is_premium:
        user = db.get_user(user_id)
        premium_until = user['premium_until']
        message = f"💎 **Премиум активна**\n\nДействует до: {premium_until}"
    else:
        message = "💎 **Подписка неактивна**\n\nОформите подписку, чтобы получить доступ ко всем функциям!"
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=settings_menu())

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать помощь"""
    message = (
        "❓ **Что умеет этот бот?**\n\n"
        "С помощью Просто Трекера вы можете планировать задачи, "
        "отслеживать привычки и двигаться вперёд без перегрузки. "
        "Просто. Понятно. Каждый день.\n\n"
        
        "**Основные функции:**\n"
        "📋 Задачи - планируйте дела на день\n"
        "🔄 Привычки - отслеживайте прогресс (Премиум)\n"
        "🎯 Цели на год - ставьте долгосрочные цели (Премиум)\n"
        "📊 Аналитика - смотрите свою продуктивность\n"
        "💎 Премиум - больше возможностей\n\n"
        
        "По всем вопросам: @support_bot"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=settings_menu())