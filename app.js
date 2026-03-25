const tg = window.Telegram.WebApp;
tg.expand();

let currentUser = tg.initDataUnsafe?.user || { id: null, first_name: 'Пользователь' };
let currentDate = new Date();
let tasksData = [];
let habitsData = [];
let goalsData = [];

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('userName').textContent = currentUser.first_name;
    setupEventListeners();
    renderCalendar();
    loadTasks();
    loadHabits();
    loadGoals();
});

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
        btn.addEventListener('click', () => switchScreen('main'));
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
    if (screen === 'main') {
        document.getElementById('mainScreen').classList.add('active');
        renderCalendar();
    } else if (screen === 'tasks') {
        document.getElementById('tasksScreen').classList.add('active');
        renderTasks();
    } else if (screen === 'habits') {
        document.getElementById('habitsScreen').classList.add('active');
        renderHabits();
    } else if (screen === 'goals') {
        document.getElementById('goalsScreen').classList.add('active');
        renderGoals();
    } else if (screen === 'analytics') {
        document.getElementById('analyticsScreen').classList.add('active');
        loadAnalytics('week');
    }
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

// Календарь
function renderCalendar() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    document.getElementById('currentMonth').textContent = `${getMonthName(month)} ${year}г.`;
    
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
        dayDiv.addEventListener('click', () => selectDate(date));
        container.appendChild(dayDiv);
    });
    
    updateWeekInfo();
}

function getMonthName(month) {
    const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
    return months[month];
}

function updateWeekInfo() {
    const now = new Date();
    const firstDayOfYear = new Date(now.getFullYear(), 0, 1);
    const pastDays = (now - firstDayOfYear) / 86400000;
    const weekNumber = Math.ceil((pastDays + firstDayOfYear.getDay() + 1) / 7);
    
    const weekStart = new Date(now);
    weekStart.setDate(now.getDate() - now.getDay() + 1);
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);
    
    document.getElementById('weekNumber').textContent = `${weekNumber} неделя`;
    document.getElementById('weekRange').textContent = `${formatDate(weekStart)} - ${formatDate(weekEnd)}`;
}

function formatDate(date) {
    return `${date.getDate()} ${getShortMonth(date.getMonth())}`;
}

function getShortMonth(month) {
    const months = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
    return months[month];
}

function selectDate(date) {
    // TODO: Показать задачи на выбранную дату
}

// Задачи
async function loadTasks() {
    const response = await sendCommand('get_tasks');
    if (response.tasks) {
        tasksData = response.tasks;
        renderTasks();
    }
}

function renderTasks() {
    const container = document.getElementById('tasksList');
    if (tasksData.length === 0) {
        container.innerHTML = '<div class="empty-state">Задач пока нет</div>';
        return;
    }
    container.innerHTML = '';
    tasksData.forEach(task => {
        const taskDiv = document.createElement('div');
        taskDiv.className = `task-item ${task.completed ? 'completed' : ''}`;
        taskDiv.innerHTML = `
            <div>
                <span class="task-title">${escapeHtml(task.title)}</span>
                ${task.important ? '<span class="important-badge">⭐ Важная</span>' : ''}
                <div style="font-size: 12px; opacity: 0.6;">${task.date || ''}</div>
            </div>
            <div class="task-actions">
                ${!task.completed ? `<button class="complete-task" data-id="${task.id}">✅</button>` : ''}
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
    const response = await sendCommand('get_habits');
    if (response.habits) {
        habitsData = response.habits;
        renderHabits();
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
            <span>${escapeHtml(habit.name)}</span>
            <div class="habit-actions">
                <button class="complete-habit" data-id="${habit.id}">✅</button>
                <button class="delete-habit" data-id="${habit.id}">🗑️</button>
            </div>
        `;
        container.appendChild(habitDiv);
    });
}

async function addHabit() {
    const name = document.getElementById('habitName').value;
    if (!name) {
        alert('Введите название привычки');
        return;
    }
    await sendCommand('add_habit', { name, days: ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ'] });
    closeAllModals();
    document.getElementById('habitName').value = '';
    loadHabits();
}

// Цели
async function loadGoals() {
    const response = await sendCommand('get_goals');
    if (response.goals) {
        goalsData = response.goals;
        renderGoals();
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
    loadGoals();
}

// Аналитика
async function loadAnalytics(period = 'week') {
    const response = await sendCommand('get_analytics', { period });
    if (response) {
        document.getElementById('analyticsTotal').textContent = response.total_tasks || 0;
        document.getElementById('analyticsCompleted').textContent = response.completed_tasks || 0;
        const percent = response.completion_rate || 0;
        document.getElementById('analyticsProgress').textContent = `${Math.round(percent)}%`;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

tg.ready();