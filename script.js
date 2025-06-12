const API_BASE = '/api';
let token = localStorage.getItem('token');

const authDiv = document.getElementById('auth');
const appDiv = document.getElementById('app');
const registerForm = document.getElementById('register-form');
const loginForm = document.getElementById('login-form');
const expenseForm = document.getElementById('expense-form');
const expensesTable = document.querySelector('#expenses-table tbody');

function showApp() {
    authDiv.classList.add('hidden');
    appDiv.classList.remove('hidden');
    loadExpenses();
}

function showAuth() {
    authDiv.classList.remove('hidden');
    appDiv.classList.add('hidden');
}

async function registerUser(e) {
    e.preventDefault();
    const res = await fetch(`${API_BASE}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: document.getElementById('reg-username').value,
            password: document.getElementById('reg-password').value
        })
    });
    if (res.ok) {
        alert('Registered! Please log in.');
    } else {
        alert('Register failed');
    }
}

async function loginUser(e) {
    e.preventDefault();
    const res = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: document.getElementById('login-username').value,
            password: document.getElementById('login-password').value
        })
    });
    if (res.ok) {
        const data = await res.json();
        token = data.token;
        localStorage.setItem('token', token);
        showApp();
    } else {
        alert('Login failed');
    }
}

async function loadExpenses() {
    const res = await fetch(`${API_BASE}/expenses`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (res.ok) {
        const expenses = await res.json();
        expensesTable.innerHTML = '';
        expenses.forEach(addExpenseRow);
    } else if (res.status === 401) {
        showAuth();
    }
}

function addExpenseRow(exp) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input data-id="${exp.id}" data-field="description" value="${exp.description}"></td>
        <td><input data-id="${exp.id}" data-field="amount" type="number" value="${exp.amount}"></td>
        <td><input data-id="${exp.id}" data-field="date" type="date" value="${exp.date.slice(0,10)}"></td>
        <td><input data-id="${exp.id}" data-field="category" value="${exp.category}"></td>
        <td>
            <button data-action="save" data-id="${exp.id}">Save</button>
            <button data-action="delete" data-id="${exp.id}">Delete</button>
        </td>`;
    expensesTable.appendChild(tr);
}

async function addExpense(e) {
    e.preventDefault();
    const res = await fetch(`${API_BASE}/expenses`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
            description: document.getElementById('exp-description').value,
            amount: parseFloat(document.getElementById('exp-amount').value),
            date: document.getElementById('exp-date').value,
            category: document.getElementById('exp-category').value
        })
    });
    if (res.ok) {
        const expense = await res.json();
        addExpenseRow(expense);
        expenseForm.reset();
    } else {
        alert('Failed to add expense');
    }
}

async function updateExpense(id, data) {
    const res = await fetch(`${API_BASE}/expenses/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        alert('Update failed');
    }
}

async function deleteExpense(id) {
    const res = await fetch(`${API_BASE}/expenses/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
    });
    if (res.ok) {
        document.querySelectorAll(`[data-id="${id}"]`).forEach(el => el.closest('tr').remove());
    } else {
        alert('Delete failed');
    }
}

registerForm.addEventListener('submit', registerUser);
loginForm.addEventListener('submit', loginUser);
expenseForm.addEventListener('submit', addExpense);

expensesTable.addEventListener('click', e => {
    if (e.target.dataset.action === 'delete') {
        deleteExpense(e.target.dataset.id);
    } else if (e.target.dataset.action === 'save') {
        const id = e.target.dataset.id;
        const row = e.target.closest('tr');
        const data = {};
        row.querySelectorAll('input').forEach(input => {
            data[input.dataset.field] = input.value;
        });
        updateExpense(id, data);
    }
});

if (token) {
    showApp();
}
