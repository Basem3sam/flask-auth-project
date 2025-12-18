from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

DATABASE = 'users.db'

app = Flask(__name__)
app.secret_key = "my_super_super_secret_key"

def get_db_connection():
  conn = sqlite3.connect(DATABASE)
  conn.row_factory = sqlite3.Row
  return conn

def init_db():
  # Initialize the database with users table
  conn = get_db_connection()
  conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL
      )
  ''')
  conn.commit()
  conn.close()

init_db()

def login_required(f):
  # Decorator to require login for certain routes
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if 'user_id' not in session:
      flash('Please log in to access this page.')
      return redirect(url_for('login'))
    return f(*args, **kwargs)
  return decorated_function

@app.route('/')
def home():
  return render_template('home.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db_connection()
    user = conn.execute(
      'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()
    conn.close()

    if user and user['password'] == password:
      session['user_id'] = user['id']
      session['username'] = user['username']
      flash(f'Welcome back, {username}!')
      return redirect(url_for('dashboard'))
    else:
      flash('Invalid username or password!')
      return redirect(url_for('login'))
  
  return render_template('login.html')

@app.route('/register', methods = ['GET', 'POST'])
def register():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    # Validation
    if not username or not password:
      flash('Username and password are required!')
      return redirect(url_for('register'))
    
    if password != confirm_password:
      flash('Passwords do not match!')
      return redirect(url_for('register'))
    
    if len(password) < 8:
      flash('Password must be at least 6 characters long!')
      return redirect(url_for('register'))


    try:
      conn = get_db_connection()
      conn.execute(
        'INSERT INTO users (username, password) VALUES (?, ?)',
        (username, password)
      )
      conn.commit()
      conn.close()
      
      flash('Registration successful! Please log in.')
      return redirect(url_for('login'))
    
    except sqlite3.IntegrityError:
      flash('Username already exists!')
      return redirect(url_for('register'))
  
  return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - requires login"""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()
    conn.close()
    
    return render_template('dashboard.html', user=user)
  
@app.route('/logout')
@login_required
def logout():
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
  app.run()