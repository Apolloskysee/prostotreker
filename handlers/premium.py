from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import database as db
from config import PREMIUM_PRICES, PREMIUM_DISCOUNTS, TRIAL_DAYS
from keyboards.keyboards import premium_keyboard, main_menu

async def show_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о премиум подписке"""
    user_id = update.effective_user.id
    is_premium_user = db.is_premium(user_id)
    
    if is_premium_user:
        user = db.get_user(user_id)
        premium_until = datetime.fromisoformat(user['premium_until'])
        days_left = (premium_until - datetime.now()).days
        
        await update.message.reply_text(
            f"💎 **Премиум активна!**\n\n"
            f"До окончания подписки осталось: {days_left} дней\n\n"
            f"Вам доступны все функции:\n"
            f"✓ Безлимитное количество задач\n"
            f"✓ Неограниченные привычки\n"
            f"✓ Заметки без лимитов\n"
            f"✓ Важные задачи\n"
            f"✓ Уведомления по задачам и привычкам\n"
            f"✓ Цели на год\n"
            f"✓ Расширенная аналитика",
            parse_mode='Markdown',
            reply_markup=main_menu()
        )
    else:
        await update.message.reply_text(
            "**💎 Премиум Трекер**\n\n"
            "Больше свободы и десятки эксклюзивных функций с подпиской Премиум.\n\n"
            f"**💰 Ежегодно** -33%\n"
            f"12 месяцев · {PREMIUM_PRICES['yearly']} ₽\n\n"
            f"**⭐ На 3 месяца** -13%\n"
            f"3 месяца · {PREMIUM_PRICES['quarterly']} ₽\n\n"
            f"**📆 Ежемесячно**\n"
            f"{PREMIUM_PRICES['monthly']} ₽/месяц",
            parse_mode='Markdown',
            reply_markup=premium_keyboard()
        )

async def handle_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора премиум подписки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "premium_monthly":
        db.activate_premium(user_id, 1)
        await query.edit_message_text(
            f"✅ Подписка Премиум активирована на 1 месяц!\n\n"
            f"Спасибо за выбор Просто Трекера!",
            reply_markup=main_menu()
        )
    
    elif data == "premium_quarterly":
        db.activate_premium(user_id, 3)
        await query.edit_message_text(
            f"✅ Подписка Премиум активирована на 3 месяца!\n\n"
            f"Спасибо за выбор Просто Трекера!",
            reply_markup=main_menu()
        )
    
    elif data == "premium_yearly":
        db.activate_premium(user_id, 12)
        await query.edit_message_text(
            f"✅ Подписка Премиум активирована на 12 месяцев!\n\n"
            f"Спасибо за выбор Просто Трекера!",
            reply_markup=main_menu()
        )
    
    elif data == "premium_trial":
        user = db.get_user(user_id)
        if user and not user['trial_used']:
            db.activate_trial(user_id)
            await query.edit_message_text(
                f"🎁 Пробный период активирован на {TRIAL_DAYS} дня!\n\n"
                f"Наслаждайтесь всеми возможностями Премиум бесплатно!",
                reply_markup=main_menu()
            )
        else:
            await query.edit_message_text(
                "❌ Пробный период уже был использован.\n\n"
                "Вы можете оформить платную подписку.",
                reply_markup=premium_keyboard()
            )
    
    elif data == "back_to_menu":
        await query.edit_message_text(
            "Главное меню",
            reply_markup=main_menu()
        )