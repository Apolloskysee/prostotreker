const tg = window.Telegram.WebApp;
tg.expand();

let currentUser = tg.initDataUnsafe?.user;

// Функция отправки команды боту и ожидания ответа
function sendCommand(command, data = {}) {
    return new Promise((resolve) => {
        const messageId = Date.now();
        // подписываемся на событие получения сообщения
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

// Загрузка данных
async function loadTasks() {
    const response = await sendCommand('get_tasks');
    if (response.tasks) {
        renderTasks(response.tasks);
    }
}

function renderTasks(tasks) {
    const container = document.getElementById('tasks-list');
    container.innerHTML = '';
    tasks.forEach(task => {
        const div = document.createElement('div');
        div.className = 'item';
        div.innerHTML = `
            <span class="item-title">${task.title} ${task.important ? '⭐' : ''}</span>
            <div class="item-actions">
                ${!task.completed ? `<button data-id="${task.id}" class="complete-task">✅</button>` : ''}
                <button data-id="${task.id}" class="delete-task">🗑️</button>
            </div>
        `;
        container.appendChild(div);
    });
    document.querySelectorAll('.complete-task').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = btn.dataset.id;
            await sendCommand('complete_task', { task_id: id });
            loadTasks(); // перезагружаем
        });
    });
    document.querySelectorAll('.delete-task').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = btn.dataset.id;
            await sendCommand('delete_task', { task_id: id });
            loadTasks();
        });
    });
}

async function loadHabits() {
    const response = await sendCommand('get_habits');
    if (response.habits) {
        renderHabits(response.habits);
    }
}

function renderHabits(habits) {
    const container = document.getElementById('habits-list');
    container.innerHTML = '';
    habits.forEach(habit => {
        const div = document.createElement('div');
        div.className = 'item';
        div.innerHTML = `
            <span class="item-title">${habit.name}</span>
            <div class="item-actions">
                <button data-id="${habit.id}" class="complete-habit">✅</button>
                <button data-id="${habit.id}" class="delete-habit">🗑️</button>
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
    document.querySelectorAll('.delete-habit').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = btn.dataset.id;
            await sendCommand('delete_habit', { habit_id: id });
            loadHabits();
        });
    });
}

async function loadGoals() {
    const response = await sendCommand('get_goals');
    if (response.goals) {
        renderGoals(response.goals);
    }
}

function renderGoals(goals) {
    const container = document.getElementById('goals-list');
    container.innerHTML = '';
    goals.forEach(goal => {
        const div = document.createElement('div');
        div.className = 'item';
        div.innerHTML = `
            <span class="item-title">${goal.title} (до ${goal.deadline})</span>
            <div class="item-actions">
                ${!goal.completed ? `<button data-id="${goal.id}" class="complete-goal">✅</button>` : ''}
                <button data-id="${goal.id}" class="delete-goal">🗑️</button>
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
    document.querySelectorAll('.delete-goal').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = btn.dataset.id;
            await sendCommand('delete_goal', { goal_id: id });
            loadGoals();
        });
    });
}

async function loadFinance() {
    const response = await sendCommand('get_finance');
    if (response.stats) {
        document.getElementById('finance-stats').innerHTML = `
            <p>Баланс: ${response.stats.balance} ₽</p>
            <p>Доходы: ${response.stats.income} ₽</p>
            <p>Расходы: ${response.stats.expense} ₽</p>
        `;
        if (response.transactions) {
            const container = document.getElementById('transactions-list');
            container.innerHTML = '';
            response.transactions.forEach(trans => {
                const div = document.createElement('div');
                div.className = 'item';
                div.innerHTML = `
                    <span>${trans.date} ${trans.description}: ${trans.amount} ₽</span>
                    <button data-id="${trans.id}" class="delete-transaction">🗑️</button>
                `;
                container.appendChild(div);
            });
            document.querySelectorAll('.delete-transaction').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const id = btn.dataset.id;
                    await sendCommand('delete_transaction', { transaction_id: id });
                    loadFinance();
                });
            });
        }
    }
}

// Добавление задач/привычек/целей/транзакций через диалог
document.getElementById('add-task').addEventListener('click', () => {
    const title = prompt('Название задачи:');
    if (title) {
        const date = prompt('Дата (ДД.ММ.ГГГГ):');
        sendCommand('add_task', { title, date }).then(() => loadTasks());
    }
});
document.getElementById('add-habit').addEventListener('click', () => {
    const name = prompt('Название привычки:');
    if (name) {
        const days = prompt('Дни (ПН, ВТ,... через запятую):');
        sendCommand('add_habit', { name, days: days.split(',') }).then(() => loadHabits());
    }
});
document.getElementById('add-goal').addEventListener('click', () => {
    const title = prompt('Название цели:');
    if (title) {
        const deadline = prompt('Срок (ДД.ММ.ГГГГ):');
        sendCommand('add_goal', { title, deadline }).then(() => loadGoals());
    }
});
document.getElementById('add-transaction').addEventListener('click', () => {
    const type = confirm('Доход? (Отмена - расход)') ? 'income' : 'expense';
    const amount = prompt('Сумма:');
    if (amount) {
        const category = prompt('Категория:');
        const description = prompt('Описание:');
        sendCommand('add_transaction', { type, amount, category, description }).then(() => loadFinance());
    }
});

// Вкладки
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        const tabId = btn.dataset.tab;
        document.getElementById(tabId).classList.add('active');
        if (tabId === 'tasks') loadTasks();
        if (tabId === 'habits') loadHabits();
        if (tabId === 'goals') loadGoals();
        if (tabId === 'finance') loadFinance();
    });
});

// Загрузка текущей вкладки при старте
loadTasks();

tg.ready();