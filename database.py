import sqlite3
import json
from datetime import datetime, timedelta
from config import DATABASE_PATH

def get_db_connection():
    """Получение соединения с базой данных"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализация базы данных"""
    with get_db_connection() as conn:
        # Пользователи
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                premium INTEGER DEFAULT 0,
                premium_until TEXT,
                trial_used INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Задачи
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                description TEXT,
                date TEXT,
                completed INTEGER DEFAULT 0,
                important INTEGER DEFAULT 0,
                reminder_time TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Привычки
        conn.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                description TEXT,
                days TEXT,
                reminder_time TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Выполнение привычек по дням
        conn.execute("""
            CREATE TABLE IF NOT EXISTS habit_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER,
                date TEXT,
                completed INTEGER DEFAULT 0,
                FOREIGN KEY (habit_id) REFERENCES habits (id)
            )
        """)
        
        # Цели на год
        conn.execute("""
            CREATE TABLE IF NOT EXISTS yearly_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                description TEXT,
                deadline TEXT,
                completed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Настройки уведомлений
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                user_id INTEGER PRIMARY KEY,
                task_reminders INTEGER DEFAULT 1,
                habit_reminders INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budget_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                type TEXT,
                color TEXT,
                icon TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category_id INTEGER,
                amount REAL,
                description TEXT,
                date TEXT,
                type TEXT,
                is_shared INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (category_id) REFERENCES budget_categories (id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS shared_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS shared_account_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                user_id INTEGER,
                role TEXT DEFAULT 'member',
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES shared_accounts (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS shared_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                category_id INTEGER,
                amount REAL,
                description TEXT,
                date TEXT,
                created_by INTEGER,
                split_type TEXT DEFAULT 'equal',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES shared_accounts (id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER,
                to_user_id INTEGER,
                amount REAL,
                description TEXT,
                transaction_id INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                paid_at TEXT,
                FOREIGN KEY (from_user_id) REFERENCES users (id),
                FOREIGN KEY (to_user_id) REFERENCES users (id)
            )
        """)
        
        
        conn.commit()

def get_user(user_id):
    """Получение информации о пользователе"""
    with get_db_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return None
        return dict(user)

def create_user(user_id, username, first_name, last_name):
    """Создание нового пользователя"""
    with get_db_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, last_name)
        )
        conn.execute(
            "INSERT OR IGNORE INTO notifications (user_id) VALUES (?)",
            (user_id,)
        )
        conn.commit()

def is_premium(user_id):
    """Проверка премиум статуса"""
    user = get_user(user_id)
    if not user:
        return False
    
    if user['premium'] and user['premium_until']:
        premium_until = datetime.fromisoformat(user['premium_until'])
        if premium_until > datetime.now():
            return True
    
    return False

def activate_premium(user_id, months):
    """Активация премиум подписки"""
    with get_db_connection() as conn:
        premium_until = (datetime.now() + timedelta(days=30*months)).isoformat()
        conn.execute(
            "UPDATE users SET premium = 1, premium_until = ? WHERE id = ?",
            (premium_until, user_id)
        )
        conn.commit()

def activate_trial(user_id):
    """Активация пробного периода"""
    with get_db_connection() as conn:
        trial_until = (datetime.now() + timedelta(days=3)).isoformat()
        conn.execute(
            "UPDATE users SET premium = 1, premium_until = ?, trial_used = 1 WHERE id = ?",
            (trial_until, user_id)
        )
        conn.commit()

# Функции для работы с задачами
def add_task(user_id, title, date, reminder_time=None, important=0):
    """Добавление задачи"""
    with get_db_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO tasks (user_id, title, date, reminder_time, important) 
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, title, date, reminder_time, important)
        )
        conn.commit()
        return cursor.lastrowid

def get_tasks_for_date(user_id, date):
    """Получение задач на конкретную дату"""
    with get_db_connection() as conn:
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND date = ? ORDER BY important DESC, id DESC",
            (user_id, date)
        ).fetchall()
        return [dict(task) for task in tasks]

def complete_task(task_id):
    """Отметка задачи как выполненной"""
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE tasks SET completed = 1 WHERE id = ?",
            (task_id,)
        )
        conn.commit()

def delete_task(task_id):
    """Удаление задачи"""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

# Функции для работы с привычками
def add_habit(user_id, name, days, reminder_time=None):
    """Добавление привычки"""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO habits (user_id, name, days, reminder_time) VALUES (?, ?, ?, ?)",
            (user_id, name, json.dumps(days), reminder_time)
        )
        conn.commit()
        return cursor.lastrowid

def get_user_habits(user_id):
    """Получение всех привычек пользователя"""
    with get_db_connection() as conn:
        habits = conn.execute(
            "SELECT * FROM habits WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        return [dict(habit) for habit in habits]

def complete_habit(habit_id, date):
    """Отметка выполнения привычки"""
    with get_db_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO habit_completions (habit_id, date, completed) 
               VALUES (?, ?, 1)""",
            (habit_id, date)
        )
        conn.commit()

def get_habit_completion(habit_id, date):
    """Проверка выполнения привычки в конкретный день"""
    with get_db_connection() as conn:
        result = conn.execute(
            "SELECT completed FROM habit_completions WHERE habit_id = ? AND date = ?",
            (habit_id, date)
        ).fetchone()
        return result['completed'] if result else 0

def delete_habit(habit_id):
    """Удаление привычки и всех её выполнений"""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        conn.execute("DELETE FROM habit_completions WHERE habit_id = ?", (habit_id,))
        conn.commit()

# Функции для работы с целями
def add_goal(user_id, title, deadline):
    """Добавление цели на год"""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO yearly_goals (user_id, title, deadline) VALUES (?, ?, ?)",
            (user_id, title, deadline)
        )
        conn.commit()
        return cursor.lastrowid

def get_user_goals(user_id):
    """Получение всех целей пользователя"""
    with get_db_connection() as conn:
        goals = conn.execute(
            "SELECT * FROM yearly_goals WHERE user_id = ? ORDER BY deadline",
            (user_id,)
        ).fetchall()
        return [dict(goal) for goal in goals]

def complete_goal(goal_id):
    """Отметка цели как выполненной"""
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE yearly_goals SET completed = 1 WHERE id = ?",
            (goal_id,)
        )
        conn.commit()

def delete_goal(goal_id):
    """Удаление цели"""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM yearly_goals WHERE id = ?", (goal_id,))
        conn.commit()

# Функции для аналитики
def get_analytics(user_id, period='week'):
    """Получение аналитики за период"""
    with get_db_connection() as conn:
        if period == 'week':
            date_from = (datetime.now() - timedelta(days=7)).isoformat()
        elif period == 'month':
            date_from = (datetime.now() - timedelta(days=30)).isoformat()
        else:  # year
            date_from = (datetime.now() - timedelta(days=365)).isoformat()
        
        tasks = conn.execute(
            """SELECT COUNT(*) as total, 
               SUM(completed) as completed 
               FROM tasks 
               WHERE user_id = ? AND date >= ?""",
            (user_id, date_from)
        ).fetchone()
        
        return {
            'total_tasks': tasks['total'] or 0,
            'completed_tasks': tasks['completed'] or 0,
            'completion_rate': (tasks['completed'] / tasks['total'] * 100) if tasks['total'] > 0 else 0
        }
    # ========== ФИНАНСОВЫЙ МОДУЛЬ ==========

def init_finance_tables():
    """Создание таблиц для финансов (вызывается отдельно или в init_db)"""
    with get_db_connection() as conn:
        # Категории (личные)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budget_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                type TEXT, -- 'income' или 'expense'
                color TEXT,
                icon TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Транзакции (личные)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category_id INTEGER,
                amount REAL,
                description TEXT,
                date TEXT,
                type TEXT,
                is_shared INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (category_id) REFERENCES budget_categories (id)
            )
        """)
        
        # Общие счета
        conn.execute("""
            CREATE TABLE IF NOT EXISTS shared_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Участники общих счетов
        conn.execute("""
            CREATE TABLE IF NOT EXISTS shared_account_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                user_id INTEGER,
                role TEXT DEFAULT 'member',
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES shared_accounts (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Общие транзакции
        conn.execute("""
            CREATE TABLE IF NOT EXISTS shared_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                category_id INTEGER,
                amount REAL,
                description TEXT,
                date TEXT,
                created_by INTEGER,
                split_type TEXT DEFAULT 'equal',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES shared_accounts (id)
            )
        """)
        
        # Долги
        conn.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER,
                to_user_id INTEGER,
                amount REAL,
                description TEXT,
                transaction_id INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                paid_at TEXT,
                FOREIGN KEY (from_user_id) REFERENCES users (id),
                FOREIGN KEY (to_user_id) REFERENCES users (id)
            )
        """)
        conn.commit()

# Добавьте вызов init_finance_tables() в init_db() после создания остальных таблиц:
# внутри init_db() после всех CREATE TABLE добавьте:
# init_finance_tables()

# Теперь функции для работы с финансами (примеры)
def add_transaction(user_id, amount, trans_type, category_name=None, description=None, date=None):
    """Добавить личную транзакцию"""
    if date is None:
        date = datetime.now().date().isoformat()
    # Найти или создать категорию
    with get_db_connection() as conn:
        if category_name:
            cat = conn.execute(
                "SELECT id FROM budget_categories WHERE user_id=? AND name=? AND type=?",
                (user_id, category_name, trans_type)
            ).fetchone()
            if cat:
                category_id = cat['id']
            else:
                cur = conn.execute(
                    "INSERT INTO budget_categories (user_id, name, type) VALUES (?, ?, ?)",
                    (user_id, category_name, trans_type)
                )
                category_id = cur.lastrowid
        else:
            category_id = None
        
        cur = conn.execute(
            "INSERT INTO transactions (user_id, category_id, amount, description, date, type, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, category_id, amount, description, date, trans_type, user_id)
        )
        conn.commit()
        return cur.lastrowid

def get_transactions(user_id, limit=20):
    """Получить последние транзакции"""
    with get_db_connection() as conn:
        rows = conn.execute(
            """SELECT t.*, bc.name as category_name, bc.icon 
               FROM transactions t
               LEFT JOIN budget_categories bc ON t.category_id = bc.id
               WHERE t.user_id = ?
               ORDER BY t.date DESC, t.id DESC
               LIMIT ?""",
            (user_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]

def get_finance_stats(user_id):
    """Получить сводку: баланс, доходы, расходы за месяц"""
    month_start = datetime.now().replace(day=1).date().isoformat()
    with get_db_connection() as conn:
        income = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id=? AND type='income' AND date >= ?",
            (user_id, month_start)
        ).fetchone()[0]
        expense = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id=? AND type='expense' AND date >= ?",
            (user_id, month_start)
        ).fetchone()[0]
        balance = income - expense
        return {'balance': balance, 'income': income, 'expense': expense}