import sqlite3

DB = 'spendwise.db'

def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # Create 'users' table if not exists
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        monthly_income REAL DEFAULT 0
    )
    ''')

    # Create 'expenses' table if not exists
    cur.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        note TEXT,
        label TEXT DEFAULT 'default',
        color TEXT DEFAULT '#3498db',
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    con.commit()  # Commit the changes to the database
    con.close()   # Close the connection to the database

if __name__ == '__main__':
    init_db()  # Initialize the database and tables
    print('Database and tables initialized successfully.')
