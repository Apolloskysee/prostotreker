import json
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

import database as db
from keyboards.keyboards import finance_menu, back_keyboard

# Состояния для ConversationHandler
(ADD_TRANSACTION_AMOUNT, ADD_TRANSACTION_CATEGORY, ADD_TRANSACTION_DESC,
 ADD_TRANSACTION_TYPE, ADD_TRANSACTION_SHARED, SELECT_SHARED_ACCOUNT,
 SPLIT_TRANSACTION, SPLIT_METHOD, SELECT_DEBT_USER) = range(9)

async def show_finance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню финансов с краткой сводкой (доступно всем)"""
    user_id = update.effective_user.id
    # Проверка премиума УБРАНА - теперь доступно всем

    stats = db.get_finance_stats(user_id)
    message = (
        "💰 **Семейный бюджет**\n\n"
        f"📊 **Баланс:** {stats['balance']:.2f} ₽\n"
        f"📈 **Доходы за месяц:** {stats['income']:.2f} ₽\n"
        f"📉 **Расходы за месяц:** {stats['expense']:.2f} ₽\n"
    )
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=finance_menu())

async def add_transaction_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать добавление транзакции"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Доход", callback_data="type_income"),
         InlineKeyboardButton("💸 Расход", callback_data="type_expense")],
        [InlineKeyboardButton("◀️ Отмена", callback_data="cancel")]
    ])
    await update.message.reply_text("Выберите тип операции:", reply_markup=keyboard)
    return ADD_TRANSACTION_TYPE

async def add_transaction_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить тип транзакции"""
    query = update.callback_query
    await query.answer()
    trans_type = query.data.split("_")[1]
    context.user_data['trans_type'] = trans_type
    await query.edit_message_text("Введите сумму (в рублях):\n\nПример: 1500.50")
    return ADD_TRANSACTION_AMOUNT

async def add_transaction_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить сумму транзакции"""
    try:
        amount = float(update.message.text.replace(',', '.'))
        context.user_data['trans_amount'] = amount
        await update.message.reply_text("Введите категорию (например, Продукты, Транспорт):")
        return ADD_TRANSACTION_CATEGORY
    except ValueError:
        await update.message.reply_text("❌ Неверный формат суммы. Введите число (например, 1500 или 1500.50):")
        return ADD_TRANSACTION_AMOUNT

async def add_transaction_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить категорию транзакции"""
    category = update.message.text.strip()
    context.user_data['trans_category'] = category
    await update.message.reply_text("Введите описание (или отправьте 'пропустить'):")
    return ADD_TRANSACTION_DESC

async def add_transaction_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить описание транзакции"""
    desc = None if update.message.text.lower() == 'пропустить' else update.message.text
    context.user_data['trans_desc'] = desc

    # Сохраняем транзакцию
    db.add_transaction(
        user_id=update.effective_user.id,
        amount=context.user_data['trans_amount'],
        trans_type=context.user_data['trans_type'],
        category_name=context.user_data['trans_category'],
        description=desc
    )

    await update.message.reply_text(
        f"✅ Транзакция добавлена!\n\n"
        f"Тип: {'💰 Доход' if context.user_data['trans_type'] == 'income' else '💸 Расход'}\n"
        f"Сумма: {context.user_data['trans_amount']:.2f} ₽\n"
        f"Категория: {context.user_data['trans_category']}\n"
        f"Описание: {desc or 'Нет'}",
        reply_markup=finance_menu()
    )
    context.user_data.clear()
    return ConversationHandler.END

async def show_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать историю транзакций (доступно всем)"""
    user_id = update.effective_user.id
    # Проверка премиума УБРАНА

    transactions = db.get_transactions(user_id, limit=20)
    if not transactions:
        await update.message.reply_text("📭 История транзакций пуста\n\n➕ Добавьте первую транзакцию!", reply_markup=finance_menu())
        return

    message = "📜 **Последние транзакции:**\n\n"
    for t in transactions:
        sign = "+" if t['type'] == 'income' else "-"
        message += f"{t['date']}: {sign}{t['amount']:.2f} ₽ - {t['category_name']} ({t['description'] or 'без описания'})\n"
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=finance_menu())

async def show_budget_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать анализ бюджета по категориям (доступно всем)"""
    user_id = update.effective_user.id
    # Проверка премиума УБРАНА

    stats = db.get_finance_stats(user_id)
    message = (
        "📊 **Аналитика расходов**\n\n"
        f"💰 Доходы за месяц: {stats['income']:.2f} ₽\n"
        f"💸 Расходы за месяц: {stats['expense']:.2f} ₽\n"
        f"💵 Баланс: {stats['balance']:.2f} ₽\n\n"
        "*Скоро появится детальная аналитика по категориям!*"
    )
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=finance_menu())

async def create_shared_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать создание общего счёта (доступно всем)"""
    await update.message.reply_text(
        "Введите имя партнёра (Telegram username) для совместного бюджета:\n\nПример: @partner_username",
        reply_markup=back_keyboard()
    )
    return SELECT_DEBT_USER

async def add_shared_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить партнёра в общий счёт"""
    partner_username = update.message.text.replace('@', '')
    user_id = update.effective_user.id

    with db.get_db_connection() as conn:
        partner = conn.execute("SELECT * FROM users WHERE username = ?", (partner_username,)).fetchone()
        if not partner:
            await update.message.reply_text(
                "❌ Пользователь не найден. Убедитесь, что он уже пользовался ботом.\n\n"
                "Попросите партнёра отправить команду /start",
                reply_markup=finance_menu()
            )
            return ConversationHandler.END

        cursor = conn.execute(
            "INSERT INTO shared_accounts (name, created_by) VALUES (?, ?)",
            (f"Семейный бюджет {user_id}", user_id)
        )
        account_id = cursor.lastrowid

        conn.execute(
            "INSERT INTO shared_account_members (account_id, user_id, role) VALUES (?, ?, ?)",
            (account_id, user_id, 'owner')
        )
        conn.execute(
            "INSERT INTO shared_account_members (account_id, user_id, role) VALUES (?, ?, ?)",
            (account_id, partner['id'], 'member')
        )
        conn.commit()

    await update.message.reply_text(
        f"✅ Совместный счёт создан!\n\n"
        f"Партнёр: @{partner_username}\n"
        f"Теперь вы можете добавлять общие траты, которые будут учитываться в семейном бюджете.",
        reply_markup=finance_menu()
    )
    context.user_data.clear()
    return ConversationHandler.END

async def show_debts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать долги (доступно всем)"""
    user_id = update.effective_user.id
    # Проверка премиума УБРАНА

    await update.message.reply_text(
        "💳 **Долги и расчёты**\n\n"
        "Функция в разработке. Скоро здесь появится учёт долгов между вами и партнёром.",
        parse_mode='Markdown',
        reply_markup=finance_menu()
    )

async def cancel_finance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена действия"""
    context.user_data.clear()
    await update.message.reply_text("Действие отменено", reply_markup=finance_menu())
    return ConversationHandler.END

# Обработчики callback-запросов для финансов
async def handle_finance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("type_"):
        trans_type = data.split("_")[1]
        context.user_data['trans_type'] = trans_type
        await query.edit_message_text("Введите сумму (в рублях):\n\nПример: 1500.50")
        return ADD_TRANSACTION_AMOUNT
    elif data == "cancel":
        await query.edit_message_text("Действие отменено")
        return ConversationHandler.END