from telegram import Bot
from datetime import datetime
import database as db

async def check_and_send_reminders(bot: Bot):
    """Проверка и отправка напоминаний"""
    try:
        today = datetime.now().date().isoformat()
        current_time = datetime.now().strftime("%H:%M")
        
        with db.get_db_connection() as conn:
            # Задачи с напоминаниями
            tasks = conn.execute(
                """SELECT t.*, u.username, u.first_name 
                   FROM tasks t 
                   JOIN users u ON t.user_id = u.id 
                   WHERE t.date = ? 
                   AND t.reminder_time = ? 
                   AND t.completed = 0""",
                (today, current_time)
            ).fetchall()
            
            for task in tasks:
                try:
                    await bot.send_message(
                        chat_id=task['user_id'],
                        text=f"🔔 Напоминание о задаче!\n\n"
                             f"📋 {task['title']}\n\n"
                             f"Не забудьте выполнить задачу!"
                    )
                except Exception as e:
                    print(f"Error sending reminder to {task['user_id']}: {e}")
            
            # Привычки с напоминаниями
            current_weekday = datetime.now().strftime("%a")
            habits = conn.execute(
                """SELECT h.*, u.username, u.first_name 
                   FROM habits h 
                   JOIN users u ON h.user_id = u.id 
                   WHERE h.reminder_time = ?""",
                (current_time,)
            ).fetchall()
            
            for habit in habits:
                import json
                days = json.loads(habit['days'])
                if current_weekday in days:
                    completion = db.get_habit_completion(habit['id'], today)
                    if not completion:
                        try:
                            await bot.send_message(
                                chat_id=habit['user_id'],
                                text=f"🔔 Напоминание о привычке!\n\n"
                                     f"🔄 {habit['name']}\n\n"
                                     f"Время выполнить привычку!"
                            )
                        except Exception as e:
                            print(f"Error sending habit reminder to {habit['user_id']}: {e}")
                            
    except Exception as e:
        print(f"Error in reminder system: {e}")

async def start_reminder_scheduler(application):
    """Запуск планировщика напоминаний"""
    # Важно: функция должна принимать context (аргумент от JobQueue)
    async def reminder_job(context):
        await check_and_send_reminders(application.bot)
    
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(reminder_job, interval=60, first=10)
    else:
        print("Warning: job_queue is not available. Reminders will not work.")