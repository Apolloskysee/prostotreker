from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    """Главное меню"""
    return ReplyKeyboardMarkup(
        [
            ["📋 Задачи", "🔄 Привычки"],
            ["🎯 Цели на год", "📊 Аналитика"],
            ["⚙️ Настройки", "💎 Премиум"]
        ],
        resize_keyboard=True
    )

def tasks_menu():
    """Меню задач"""
    return ReplyKeyboardMarkup(
        [
            ["➕ Добавить задачу"],
            ["📅 Задачи на сегодня", "⭐ Важные задачи"],
            ["◀️ Назад"]
        ],
        resize_keyboard=True
    )

def habits_menu():
    """Меню привычек"""
    return ReplyKeyboardMarkup(
        [
            ["➕ Добавить привычку"],
            ["📊 Мои привычки", "✅ Отметить выполнение"],
            ["◀️ Назад"]
        ],
        resize_keyboard=True
    )

def goals_menu():
    """Меню целей"""
    return ReplyKeyboardMarkup(
        [
            ["➕ Добавить цель"],
            ["🎯 Мои цели", "✅ Выполненные цели"],
            ["◀️ Назад"]
        ],
        resize_keyboard=True
    )

def settings_menu():
    """Меню настроек"""
    return ReplyKeyboardMarkup(
        [
            ["👤 Профиль", "💎 Подписка"],
            ["🔔 Уведомления", "⚙️ Предпочтения"],
            ["❓ Помощь", "◀️ Назад"]
        ],
        resize_keyboard=True
    )
def finance_menu():
    """Меню финансов"""
    return ReplyKeyboardMarkup(
        [
            ["💰 Добавить трату", "💵 Добавить доход"],
            ["📊 Аналитика", "📜 История"],
            ["👥 Совместный бюджет", "💳 Долги"],
            ["◀️ Назад"]
        ],
        resize_keyboard=True
    )

def premium_keyboard():
    """Клавиатура для премиум"""
    keyboard = [
        [InlineKeyboardButton("💰 Ежемесячно - 249₽", callback_data="premium_monthly")],
        [InlineKeyboardButton("⭐ На 3 месяца - 649₽ (-13%)", callback_data="premium_quarterly")],
        [InlineKeyboardButton("🎉 Ежегодно - 1999₽ (-33%)", callback_data="premium_yearly")],
        [InlineKeyboardButton("🎁 Пробный период 3 дня", callback_data="premium_trial")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def task_actions_keyboard(task_id):
    """Клавиатура действий с задачей"""
    keyboard = [
        [InlineKeyboardButton("✅ Выполнено", callback_data=f"complete_task_{task_id}")],
        [InlineKeyboardButton("❌ Удалить", callback_data=f"delete_task_{task_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_tasks")]
    ]
    return InlineKeyboardMarkup(keyboard)

def habit_actions_keyboard(habit_id):
    """Клавиатура действий с привычкой"""
    keyboard = [
        [InlineKeyboardButton("✅ Отметить выполнение", callback_data=f"complete_habit_{habit_id}")],
        [InlineKeyboardButton("❌ Удалить", callback_data=f"delete_habit_{habit_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_habits")]
    ]
    return InlineKeyboardMarkup(keyboard)

def goal_actions_keyboard(goal_id):
    """Клавиатура действий с целью"""
    keyboard = [
        [InlineKeyboardButton("✅ Выполнено", callback_data=f"complete_goal_{goal_id}")],
        [InlineKeyboardButton("❌ Удалить", callback_data=f"delete_goal_{goal_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_goals")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard():
    """Кнопка назад"""
    return ReplyKeyboardMarkup([["◀️ Назад"]], resize_keyboard=True)