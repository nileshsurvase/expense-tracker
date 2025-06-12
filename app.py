import sqlite3
from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret-key'
app.config['DATABASE'] = 'database.db'

# ----- Database Setup -----

def init_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    date TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )''')
    conn.commit()
    conn.close()

init_db()

# ----- Helper Functions -----

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# ----- Auth Routes -----

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                  (username, generate_password_hash(password)))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Username already exists'}), 400
    conn.close()
    return jsonify({'message': 'User created'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        return jsonify({'message': 'Logged in'})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'})

# ----- Expense Routes -----

def login_required(func):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route('/expenses', methods=['POST'])
@login_required
def add_expense():
    data = request.json
    amount = data.get('amount')
    description = data.get('description', '')
    date = data.get('date', '')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO expenses (user_id, amount, description, date) VALUES (?, ?, ?, ?)',
              (session['user_id'], amount, description, date))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Expense added'}), 201

@app.route('/expenses', methods=['GET'])
@login_required
def get_expenses():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM expenses WHERE user_id = ?', (session['user_id'],))
    expenses = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(expenses)

@app.route('/expenses/<int:expense_id>', methods=['PUT'])
@login_required
def edit_expense(expense_id):
    data = request.json
    amount = data.get('amount')
    description = data.get('description')
    date = data.get('date')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''UPDATE expenses SET amount = ?, description = ?, date = ?
                 WHERE id = ? AND user_id = ?''',
              (amount, description, date, expense_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Expense updated'})

@app.route('/expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM expenses WHERE id = ? AND user_id = ?',
              (expense_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Expense deleted'})

if __name__ == '__main__':
    app.run(debug=True)
