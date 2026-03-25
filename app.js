const tg = window.Telegram.WebApp;
tg.expand();

let currentUser = tg.initDataUnsafe?.user || { first_name: 'Пользователь' };

// Обновляем дату
function updateDate() {
    const now = new Date();
    const options = { weekday: 'short', day: 'numeric', month: 'short' };
    const formatted = now.toLocaleDateString('ru-RU', options);
    document.getElementById('currentDay').textContent = formatted;
    document.getElementById('userName').textContent = currentUser.first_name;
}
updateDate();

// Функция отправки команд боту
function sendCommand(command, data = {}) {
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

// Загрузка задач
async function loadTasks() {
    const response = await sendCommand('get_tasks');
    if (response.tasks) {
        renderTasks(response.tasks);
        updateProgress(response.tasks);
    }
}

function renderTasks(tasks) {
    const container = document.getElementById('tasks-list');
    if (!tasks.length) {
        container.innerHTML = '<p style="text-align:center; opacity:0.7;">На сегодня задач нет</p>';
        return;
    }
    container.innerHTML = '';
    tasks.forEach(task => {
        const div = document.createElement('div');
        div.className = 'task-item';
        div.innerHTML = `
            <span class="task-title">${task.title} ${task.important ? '⭐' : ''}</span>
            <div class="task-actions">
                ${!task.completed ? `<button class="complete-btn" data-id="${task.id}">✅</button>` : ''}
                <button class="delete-btn" data-id="${task.id}">🗑️</button>
            </div>
        `;
        container.appendChild(div);
    });
    
    document.querySelectorAll('.complete-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = btn.dataset.id;
            await sendCommand('complete_task', { task_id: id });
            loadTasks();
        });
    });
    
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = btn.dataset.id;
            await sendCommand('delete_task', { task_id: id });
            loadTasks();
        });
    });
}

function updateProgress(tasks) {
    const total = tasks.length;
    const completed = tasks.filter(t => t.completed).length;
    const percent = total > 0 ? (completed / total) * 100 : 0;
    
    document.getElementById('totalTasks').textContent = total;
    document.getElementById('completedTasks').textContent = completed;
    document.getElementById('progressFill').style.width = `${percent}%`;
}

// Загрузка привычек
async function loadHabits() {
    const response = await sendCommand('get_habits');
    if (response.habits) {
        const container = document.getElementById('habits-list');
        if (!response.habits.length) {
            container.innerHTML = '<p style="text-align:center; opacity:0.7;">Привычек пока нет</p>';
            return;
        }
        container.innerHTML = '';
        response.habits.forEach(habit => {
            const div = document.createElement('div');
            div.className = 'habit-item';
            div.innerHTML = `
                <span>${habit.name}</span>
                <div>
                    <button class="complete-habit" data-id="${habit.id}">✅</button>
                    <button class="delete-habit" data-id="${habit.id}">🗑️</button>
                </div>
            `;
            container.appendChild(div);
        });
        
        document.querySelectorAll('.complete-habit').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = btn.dataset.id;
                await sendCommand('complete_habit', { habit_id: id });
                loadHabits();
            });
        });
    }
}

// Загрузка целей
async function loadGoals() {
    const response = await sendCommand('get_goals');
    if (response.goals) {
        const container = document.getElementById('goals-list');
        if (!response.goals.length) {
            container.innerHTML = '<p style="text-align:center; opacity:0.7;">Целей пока нет</p>';
            return;
        }
        container.innerHTML = '';
        response.goals.forEach(goal => {
            const div = document.createElement('div');
            div.className = 'goal-item';
            div.innerHTML = `
                <span>${goal.title} (до ${goal.deadline})</span>
                <div>
                    ${!goal.completed ? `<button class="complete-goal" data-id="${goal.id}">✅</button>` : ''}
                    <button class="delete-goal" data-id="${goal.id}">🗑️</button>
                </div>
            `;
            container.appendChild(div);
        });
        
        document.querySelectorAll('.complete-goal').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = btn.dataset.id;
                await sendCommand('complete_goal', { goal_id: id });
                loadGoals();
            });
        });
    }
}

// Аналитика
let currentPeriod = 'week';
async function loadAnalytics() {
    const response = await sendCommand('get_analytics', { period: currentPeriod });
    if (response) {
        const percent = response.completion_rate || 0;
        document.getElementById('analyticsPercent').textContent = `${Math.round(percent)}%`;
        document.getElementById('analyticsTotal').textContent = response.total_tasks || 0;
        document.getElementById('analyticsCompleted').textContent = response.completed_tasks || 0;
        document.getElementById('analyticsUncompleted').textContent = (response.total_tasks - response.completed_tasks) || 0;
        document.getElementById('analyticsProgress').textContent = Math.round(percent);
        
        // Дни недели
        const weekDays = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'];
        const container = document.getElementById('weekStats');
        container.innerHTML = weekDays.map(day => `
            <div class="week-day">
                <div>${day}</div>
                <div>0/0</div>
            </div>
        `).join('');
    }
}

// Добавление задач
document.getElementById('addTaskBtn').addEventListener('click', () => {
    const title = prompt('Название задачи:');
    if (title) {
        sendCommand('add_task', { title }).then(() => loadTasks());
    }
});

document.getElementById('addHabitBtn').addEventListener('click', () => {
    const name = prompt('Название привычки:');
    if (name) {
        const days = prompt('Дни (ПН, ВТ, СР, ЧТ, ПТ, СБ, ВС через запятую):');
        sendCommand('add_habit', { name, days: days ? days.split(',') : ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ'] }).then(() => loadHabits());
    }
});

document.getElementById('addGoalBtn').addEventListener('click', () => {
    const title = prompt('Название цели:');
    if (title) {
        const deadline = prompt('Срок (ДД.ММ.ГГГГ):');
        sendCommand('add_goal', { title, deadline }).then(() => loadGoals());
    }
});

// Навигация между вкладками
document.querySelectorAll('.menu-item').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        document.querySelectorAll('.menu-item').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        if (tab === 'tasks') {
            document.querySelectorAll('.tab-page').forEach(p => p.style.display = 'none');
            document.querySelector('.app-container').style.display = 'block';
            loadTasks();
        } else if (tab === 'habits') {
            document.querySelector('.app-container').style.display = 'none';
            document.getElementById('habits-tab').style.display = 'block';
            loadHabits();
        } else if (tab === 'goals') {
            document.querySelector('.app-container').style.display = 'none';
            document.getElementById('goals-tab').style.display = 'block';
            loadGoals();
        } else if (tab === 'analytics') {
            document.querySelector('.app-container').style.display = 'none';
            document.getElementById('analytics-tab').style.display = 'block';
            loadAnalytics();
        }
    });
});

// Кнопка назад
document.querySelectorAll('.back-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-page').forEach(p => p.style.display = 'none');
        document.querySelector('.app-container').style.display = 'block';
        document.querySelector('.menu-item[data-tab="tasks"]').classList.add('active');
        loadTasks();
    });
});

// Настройки
document.getElementById('settingsBtn').addEventListener('click', () => {
    document.querySelector('.app-container').style.display = 'none';
    document.getElementById('settings-tab').style.display = 'block';
});

document.getElementById('premiumBtn').addEventListener('click', () => {
    document.getElementById('premiumModal').style.display = 'flex';
});

document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
        document.getElementById('premiumModal').style.display = 'none';
    });
});

// Периоды аналитики
document.querySelectorAll('.period-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentPeriod = btn.dataset.period;
        loadAnalytics();
    });
});

// Загрузка начальных данных
loadTasks();

tg.ready();