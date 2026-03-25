from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import database as db
from keyboards.keyboards import main_menu

async def show_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать аналитику"""
    user_id = update.effective_user.id
    
    # Получаем аналитику за разные периоды
    week_stats = db.get_analytics(user_id, 'week')
    month_stats = db.get_analytics(user_id, 'month')
    year_stats = db.get_analytics(user_id, 'year')
    
    # Создаем сообщение с аналитикой
    message = (
        "📊 **Аналитика**\n\n"
        
        "**Неделя**\n"
        f"📝 Всего задач: {week_stats['total_tasks']}\n"
        f"✅ Выполнено: {week_stats['completed_tasks']}\n"
        f"📈 Прогресс: {week_stats['completion_rate']:.1f}%\n\n"
        
        "**Месяц**\n"
        f"📝 Всего задач: {month_stats['total_tasks']}\n"
        f"✅ Выполнено: {month_stats['completed_tasks']}\n"
        f"📈 Прогресс: {month_stats['completion_rate']:.1f}%\n\n"
        
        "**Год**\n"
        f"📝 Всего задач: {year_stats['total_tasks']}\n"
        f"✅ Выполнено: {year_stats['completed_tasks']}\n"
        f"📈 Прогресс: {year_stats['completion_rate']:.1f}%"
    )
    
    # Добавляем информацию о продуктивных днях (если есть премиум)
    if db.is_premium(user_id):
        message += "\n\n💪 **Продуктивный день**: ПН"
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=main_menu())