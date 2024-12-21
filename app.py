import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup
def init_db():
    with sqlite3.connect('secretsanta.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS participants (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL
                        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS assignments (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            giver_username TEXT UNIQUE NOT NULL,
                            receiver_username TEXT NOT NULL,
                            FOREIGN KEY (giver_username) REFERENCES participants(username),
                            FOREIGN KEY (receiver_username) REFERENCES participants(username)
                        )''')
        conn.commit()

# Initialize the database
init_db()

# Helper function to get DB connection
def get_db_connection():
    return sqlite3.connect('secretsanta.db')

# Home Page
@app.route('/')
def home():
    return render_template('home.html')

# Coordinator: Register Participants
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO participants (name, username, password) VALUES (?, ?, ?)', (name, username, password))
            conn.commit()
            conn.close()
            flash('Participant registered successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'error')
        return redirect(url_for('register'))
    return render_template('register.html')

# Coordinator: Assign Secret Santa
@app.route('/assign', methods=['POST'])
def assign():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM participants')
    usernames = [row[0] for row in cursor.fetchall()]
    if len(usernames) < 2:
        flash('Need at least 2 participants to assign Secret Santa.')
        return redirect(url_for('home'))
    
    random.shuffle(usernames)
    assignments = [(usernames[i], usernames[(i + 1) % len(usernames)]) for i in range(len(usernames))]

    # Store assignments in the database
    cursor.execute('DELETE FROM assignments')  # Clear previous assignments
    cursor.executemany('INSERT INTO assignments (giver_username, receiver_username) VALUES (?, ?)', assignments)
    conn.commit()
    conn.close()

    flash('Secret Santa assignments completed!')
    return redirect(url_for('home'))

# Participant Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM participants WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        flash('Invalid credentials. Please try again.')
        return redirect(url_for('login'))
    return render_template('login.html')

# Participant Dashboard
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT receiver_username FROM assignments WHERE giver_username = ?', (username,))
    assigned_to = cursor.fetchone()
    conn.close()
    assigned_to = assigned_to[0] if assigned_to else "Not assigned yet"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM participants WHERE username = ?', (username,))
    name = cursor.fetchone()[0]
    conn.close()
    return render_template('dashboard.html', name=name, assigned_to=assigned_to)
@app.route('/participants', methods=['GET', 'POST'])
def participants_list():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Handle deletion request
    if request.method == 'POST':
        username_to_delete = request.form['username']
        cursor.execute('DELETE FROM participants WHERE username = ?', (username_to_delete,))
        cursor.execute('DELETE FROM assignments WHERE giver_username = ? OR receiver_username = ?', 
                       (username_to_delete, username_to_delete))
        conn.commit()
        flash(f'Participant {username_to_delete} deleted successfully.', 'success')

    # Fetch updated list of participants
    cursor.execute('SELECT username, name FROM participants')
    participants = cursor.fetchall()
    conn.close()

    return render_template('participants.html', participants=participants)
# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
