import os

TOKEN = "8639286175:AAFeNRCUTX1q99hnPtHqSjnz-YMAphAwB2c"  # Замените на токен вашего бота

# Цены на подписку (в рублях)
PREMIUM_PRICES = {
    "monthly": 249,
    "quarterly": 649,
    "yearly": 1999
}

# Скидки в процентах
PREMIUM_DISCOUNTS = {
    "quarterly": 13,
    "yearly": 33
}

# Пробный период (дней)
TRIAL_DAYS = 3

# База данных
DATABASE_PATH = "tracker.db"