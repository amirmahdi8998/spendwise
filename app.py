from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
from dateutil import parser
from werkzeug.security import generate_password_hash, check_password_hash

DB = 'spendwise.db'

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Used for session management and flash messages

# Helper function to get a connection to the database
def get_db_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row  # Allows column access by name
    return conn

# Route to set the user's monthly income
@app.route('/set_income', methods=['GET', 'POST'])
def set_income():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    if request.method == 'POST':
        monthly_income = request.form.get('monthly_income', '0').strip()

        # Validate monthly income input
        try:
            monthly_income_val = float(monthly_income)
        except ValueError:
            flash('Please enter a valid number for monthly income.')
            return redirect(url_for('set_income'))

        try:
            conn = get_db_conn()
            cur = conn.cursor()
            # Update the monthly income for the logged-in user
            cur.execute(
                'UPDATE users SET monthly_income = ? WHERE id = ?',
                (monthly_income_val, session['user_id'])
            )
            conn.commit()
            conn.close()
            flash('Monthly income updated successfully.')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"An error occurred: {e}")
            print(e)
            return redirect(url_for('set_income'))

    # Render the form to set monthly income
    return render_template('set_income.html')


# Route to display the user's expenses, monthly income, and remaining balance
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    user_id = session['user_id']
    conn = get_db_conn()
    cur = conn.cursor()

    # Fetch all expenses for the logged-in user
    cur.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC', (user_id,))
    expenses = cur.fetchall()

    # Calculate total expenses
    cur.execute('SELECT SUM(amount) as total FROM expenses WHERE user_id = ?', (user_id,))
    total_row = cur.fetchone()
    total = total_row['total'] if total_row and total_row['total'] is not None else 0

    # Fetch user's monthly income
    cur.execute('SELECT monthly_income FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()
    monthly_income = user['monthly_income'] if user and user['monthly_income'] is not None else 0

    # Calculate remaining balance
    remaining_balance = monthly_income - total

    conn.close()

    # Render the index page with all necessary variables
    return render_template(
        'index.html',
        expenses=expenses,
        total=total,
        monthly_income=monthly_income,
        remaining_balance=remaining_balance
    )


# Route to register a new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()  # Get the username from the form
        password = request.form.get('password')  # Get the password from the form
        confirm_password = request.form.get('confirm_password')  # Confirm password field

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match.')  # Show error if passwords don't match
            return redirect(url_for('register'))  # Redirect back to registration page

        # Hash the password before storing it in the database
        password_hash = generate_password_hash(password)

        conn = get_db_conn()
        cur = conn.cursor()
        try:
            # Insert the new user into the database
            cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password_hash))
            conn.commit()
            flash('Registration successful, please log in.')  # Notify user of successful registration
            return redirect(url_for('login'))  # Redirect to login page after successful registration
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another one.')  # Handle username duplication
        except Exception as e:
            flash(f"An error occurred: {str(e)}")  # Handle any other errors
        finally:
            conn.close()

    return render_template('register.html')  # Render the registration page

# Route to log in
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()  # Get the username
        password = request.form.get('password')  # Get the password

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cur.fetchone()

        # Check if the user exists and password matches
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))  # Redirect to the home page after login
        else:
            flash('Invalid username or password.')

        conn.close()

    return render_template('login.html')  # Render the login page

# Route to change password
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if the user is not logged in

    if request.method == 'POST':
        current_password = request.form.get('current_password')  # Get current password from form
        new_password = request.form.get('new_password')  # Get new password from form
        confirm_password = request.form.get('confirm_password')  # Confirm new password

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute('SELECT password FROM users WHERE id = ?', (session['user_id'],))
        user = cur.fetchone()

        # Check if the current password matches the stored password
        if user and check_password_hash(user['password'], current_password):
            if new_password == confirm_password:
                new_password_hash = generate_password_hash(new_password)
                cur.execute('UPDATE users SET password = ? WHERE id = ?', (new_password_hash, session['user_id']))
                conn.commit()
                flash('Password changed successfully.')
                return redirect(url_for('index'))  # Redirect to home page after password change
            else:
                flash('Passwords do not match.')
        else:
            flash('Current password is incorrect.')

        conn.close()

    return render_template('change_password.html')  # Render the change password page

# Route to log out
@app.route('/logout')
def logout():
    session.clear()  # Clear the session to log out the user
    return redirect(url_for('login'))  # Redirect to login page after logging out

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip() or 'Other'
        amount = request.form.get('amount', '0').strip()
        date_in = request.form.get('date', '').strip()
        note = request.form.get('note', '').strip()
        label = request.form.get('label', 'default').strip()

        try:
            amount_val = float(amount)
        except ValueError:
            flash('Please enter a valid number for amount.')
            return redirect(url_for('add'))

        if not date_in:
            date_str = datetime.now().strftime('%Y-%m-%d')
        else:
            try:
                dt = parser.parse(date_in)
                date_str = dt.strftime('%Y-%m-%d')
            except Exception:
                flash('Invalid date format. Use YYYY-MM-DD or similar.')
                return redirect(url_for('add'))

        conn = get_db_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                'INSERT INTO expenses (user_id, title, category, amount, date, note, label) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (user_id, title, category, amount_val, date_str, note, label)
            )
            conn.commit()
            flash('Expense added successfully.')
        except Exception as e:
            flash(f"An error occurred: {e}")
            print(e)
        finally:
            conn.close()

        return redirect(url_for('index'))

    # --- GET request: calculate monthly income and remaining balance ---
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute('SELECT monthly_income FROM users WHERE id = ?', (user_id,))
    row = cur.fetchone()
    monthly_income = row[0] if row and row[0] is not None else 0

    cur.execute('SELECT SUM(amount) FROM expenses WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    total_expenses = row[0] if row and row[0] is not None else 0

    remaining_balance = monthly_income - total_expenses
    conn.close()

    return render_template(
        'add.html',
        monthly_income=monthly_income,
        remaining_balance=remaining_balance
    )



# Route to delete an expense
@app.route('/delete/<int:exp_id>', methods=['POST'])
def delete(exp_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM expenses WHERE id = ?', (exp_id,))
    conn.commit()  # Commit the deletion
    conn.close()
    flash('Expense removed.')
    return redirect(url_for('index'))  # Redirect back to the index page after deletion

# Start the Flask application
if __name__ == '__main__':
    app.run(debug=True)
