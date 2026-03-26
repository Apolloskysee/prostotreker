const tg = window.Telegram.WebApp;
tg.expand();

let currentUser = tg.initDataUnsafe?.user || { id: null, first_name: 'Пользователь' };
let currentDate = new Date();
let tasksData = [];
let habitsData = [];
let goalsData = [];

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    updateDateInfo();
    document.getElementById('userName').textContent = currentUser.first_name;
    setupEventListeners();
    loadTasks();
    loadHabits();
    loadGoals();
    renderCalendar();
});

function updateDateInfo() {
    const now = new Date();
    const days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
    const months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
    document.getElementById('dayName').textContent = days[now.getDay()];
    document.getElementById('fullDate').textContent = `${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()}`;
}

function setupEventListeners() {
    // Навигация по меню
    document.querySelectorAll('.menu-item').forEach(btn => {
        btn.addEventListener('click', () => {
            const screen = btn.dataset.screen;
            switchScreen(screen);
        });
    });
    
    // Кнопки назад
    document.querySelectorAll('.back-btn').forEach(btn => {
        btn.addEventListener('click', () => switchScreen('tasks'));
    });
    
    // Настройки
    document.getElementById('settingsBtn').addEventListener('click', () => openModal('settingsModal'));
    document.getElementById('premiumBtn').addEventListener('click', () => openModal('premiumModal'));
    
    // Календарь
    document.getElementById('prevMonth').addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar();
    });
    document.getElementById('nextMonth').addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar();
    });
    
    // Добавление
    document.getElementById('addTaskBtn').addEventListener('click', () => openModal('addTaskModal'));
    document.getElementById('addHabitBtn').addEventListener('click', () => openModal('addHabitModal'));
    document.getElementById('addGoalBtn').addEventListener('click', () => openModal('addGoalModal'));
    
    // Отправка форм
    document.getElementById('submitTaskBtn').addEventListener('click', addTask);
    document.getElementById('submitHabitBtn').addEventListener('click', addHabit);
    document.getElementById('submitGoalBtn').addEventListener('click', addGoal);
    
    // Закрытие модалок
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', () => closeAllModals());
    });
    
    // Периоды аналитики
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadAnalytics(btn.dataset.period);
        });
    });
}

function switchScreen(screen) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    if (screen === 'tasks') {
        document.getElementById('mainScreen').classList.add('active');
        loadTasks();
    } else if (screen === 'habits') {
        document.getElementById('habitsScreen').classList.add('active');
        loadHabits();
    } else if (screen === 'goals') {
        document.getElementById('goalsScreen').classList.add('active');
        loadGoals();
    } else if (screen === 'calendar') {
        document.getElementById('calendarScreen').classList.add('active');
        renderCalendar();
    } else if (screen === 'analytics') {
        document.getElementById('analyticsScreen').classList.add('active');
        loadAnalytics('week');
    }
    
    // Обновляем активный пункт меню
    document.querySelectorAll('.menu-item').forEach(btn => {
        if (btn.dataset.screen === screen) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function openModal(modalId) {
    closeAllModals();
    document.getElementById(modalId).style.display = 'flex';
}

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
}

// Функция отправки команд боту
async function sendCommand(command, data = {}) {
    return new Promise((resolve) => {
        const messageId = Date.now();
        const handler = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.message_id === messageId) {
                    tg.offEvent('message', handler);
                    resolve(message);
                }
            } catch (e) {}
        };
        tg.onEvent('message', handler);
        tg.sendData(JSON.stringify({
            message_id: messageId,
            command: command,
            ...data
        }));
    });
}

// Задачи
async function loadTasks() {
    try {
        const response = await sendCommand('get_tasks');
        if (response && response.tasks) {
            tasksData = response.tasks;
            renderTasks();
            updateProgress();
        }
    } catch (error) {
        console.error('Ошибка загрузки задач:', error);
    }
}

function renderTasks() {
    const container = document.getElementById('tasksList');
    const activeTasks = tasksData.filter(t => !t.completed);
    
    if (activeTasks.length === 0) {
        container.innerHTML = '<div class="empty-state">На сегодня задач нет</div>';
        return;
    }
    
    container.innerHTML = '';
    activeTasks.forEach(task => {
        const taskDiv = document.createElement('div');
        taskDiv.className = 'task-item';
        taskDiv.innerHTML = `
            <div>
                <span class="task-title">${escapeHtml(task.title)}</span>
                ${task.important ? '<span class="important-badge">⭐ Важная</span>' : ''}
                ${task.date ? `<div style="font-size: 12px; opacity: 0.6;">${task.date}</div>` : ''}
            </div>
            <div class="task-actions">
                <button class="complete-task" data-id="${task.id}">✅</button>
                <button class="delete-task" data-id="${task.id}">🗑️</button>
            </div>
        `;
        container.appendChild(taskDiv);
    });
    
    document.querySelectorAll('.complete-task').forEach(btn => {
        btn.addEventListener('click', () => completeTask(btn.dataset.id));
    });
    document.querySelectorAll('.delete-task').forEach(btn => {
        btn.addEventListener('click', () => deleteTask(btn.dataset.id));
    });
}

function updateProgress() {
    const completed = tasksData.filter(t => t.completed).length;
    const total = tasksData.length;
    const percent = total > 0 ? (completed / total) * 100 : 0;
    document.getElementById('completedCount').textContent = completed;
    document.getElementById('totalCount').textContent = total;
    document.getElementById('progressFill').style.width = `${percent}%`;
}

async function addTask() {
    const title = document.getElementById('taskTitle').value;
    const date = document.getElementById('taskDate').value;
    if (!title) {
        alert('Введите название задачи');
        return;
    }
    await sendCommand('add_task', { title, date });
    closeAllModals();
    document.getElementById('taskTitle').value = '';
    document.getElementById('taskDate').value = '';
    loadTasks();
}

async function completeTask(taskId) {
    await sendCommand('complete_task', { task_id: taskId });
    loadTasks();
}

async function deleteTask(taskId) {
    if (confirm('Удалить задачу?')) {
        await sendCommand('delete_task', { task_id: taskId });
        loadTasks();
    }
}

// Привычки
async function loadHabits() {
    try {
        const response = await sendCommand('get_habits');
        if (response && response.habits) {
            habitsData = response.habits;
            renderHabits();
        }
    } catch (error) {
        console.error('Ошибка загрузки привычек:', error);
    }
}

function renderHabits() {
    const container = document.getElementById('habitsList');
    if (habitsData.length === 0) {
        container.innerHTML = '<div class="empty-state">Привычек пока нет</div>';
        return;
    }
    container.innerHTML = '';
    habitsData.forEach(habit => {
        const habitDiv = document.createElement('div');
        habitDiv.className = 'habit-item';
        habitDiv.innerHTML = `
            <div>
                <span>${escapeHtml(habit.name)}</span>
            </div>
            <div class="habit-actions">
                <button class="complete-habit" data-id="${habit.id}">✅</button>
                <button class="delete-habit" data-id="${habit.id}">🗑️</button>
            </div>
        `;
        container.appendChild(habitDiv);
    });
    
    document.querySelectorAll('.complete-habit').forEach(btn => {
        btn.addEventListener('click', () => completeHabit(btn.dataset.id));
    });
    document.querySelectorAll('.delete-habit').forEach(btn => {
        btn.addEventListener('click', () => deleteHabit(btn.dataset.id));
    });
}

async function addHabit() {
    const name = document.getElementById('habitName').value;
    if (!name) {
        alert('Введите название привычки');
        return;
    }
    await sendCommand('add_habit', { name, days: ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'] });
    closeAllModals();
    document.getElementById('habitName').value = '';
    loadHabits();
}

async function completeHabit(habitId) {
    await sendCommand('complete_habit', { habit_id: habitId });
    loadHabits();
}

async function deleteHabit(habitId) {
    if (confirm('Удалить привычку?')) {
        await sendCommand('delete_habit', { habit_id: habitId });
        loadHabits();
    }
}

// Цели
async function loadGoals() {
    try {
        const response = await sendCommand('get_goals');
        if (response && response.goals) {
            goalsData = response.goals;
            renderGoals();
        }
    } catch (error) {
        console.error('Ошибка загрузки целей:', error);
    }
}

function renderGoals() {
    const container = document.getElementById('goalsList');
    if (goalsData.length === 0) {
        container.innerHTML = '<div class="empty-state">Целей пока нет</div>';
        return;
    }
    container.innerHTML = '';
    goalsData.forEach(goal => {
        const goalDiv = document.createElement('div');
        goalDiv.className = `goal-item ${goal.completed ? 'completed' : ''}`;
        goalDiv.innerHTML = `
            <div>
                <div>${escapeHtml(goal.title)}</div>
                <div style="font-size: 12px; opacity: 0.6;">Срок: ${goal.deadline || 'Не указан'}</div>
            </div>
            <div class="goal-actions">
                ${!goal.completed ? `<button class="complete-goal" data-id="${goal.id}">✅</button>` : ''}
                <button class="delete-goal" data-id="${goal.id}">🗑️</button>
            </div>
        `;
        container.appendChild(goalDiv);
    });
    
    document.querySelectorAll('.complete-goal').forEach(btn => {
        btn.addEventListener('click', () => completeGoal(btn.dataset.id));
    });
    document.querySelectorAll('.delete-goal').forEach(btn => {
        btn.addEventListener('click', () => deleteGoal(btn.dataset.id));
    });
}

async function addGoal() {
    const title = document.getElementById('goalTitle').value;
    const deadline = document.getElementById('goalDeadline').value;
    if (!title) {
        alert('Введите название цели');
        return;
    }
    await sendCommand('add_goal', { title, deadline });
    closeAllModals();
    document.getElementById('goalTitle').value = '';
    document.getElementById('goalDeadline').value = '';
    loadGoals();
}

async function completeGoal(goalId) {
    await sendCommand('complete_goal', { goal_id: goalId });
    loadGoals();
}

async function deleteGoal(goalId) {
    if (confirm('Удалить цель?')) {
        await sendCommand('delete_goal', { goal_id: goalId });
        loadGoals();
    }
}

// Календарь
function renderCalendar() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
    document.getElementById('currentMonth').textContent = `${months[month]} ${year}г.`;
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(firstDay.getDate() - (firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1));
    
    const days = [];
    for (let i = 0; i < 42; i++) {
        const date = new Date(startDate);
        date.setDate(startDate.getDate() + i);
        days.push(date);
    }
    
    const container = document.getElementById('calendarDays');
    container.innerHTML = '';
    days.forEach(date => {
        const dayDiv = document.createElement('div');
        dayDiv.className = 'calendar-day';
        if (date.getMonth() !== month) dayDiv.classList.add('other-month');
        if (date.toDateString() === new Date().toDateString()) dayDiv.classList.add('today');
        dayDiv.textContent = date.getDate();
        container.appendChild(dayDiv);
    });
}

// Аналитика
async function loadAnalytics(period = 'week') {
    try {
        const response = await sendCommand('get_analytics', { period });
        if (response) {
            document.getElementById('analyticsTotal').textContent = response.total_tasks || 0;
            document.getElementById('analyticsCompleted').textContent = response.completed_tasks || 0;
            const percent = response.completion_rate || 0;
            document.getElementById('analyticsProgress').textContent = `${Math.round(percent)}%`;
        }
    } catch (error) {
        console.error('Ошибка загрузки аналитики:', error);
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

tg.ready();