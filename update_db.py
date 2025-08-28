import sqlite3

DB = 'spendwise.db'

def update_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # Add the monthly_income field if it doesn't exist
    try:
        cur.execute('ALTER TABLE users ADD COLUMN monthly_income REAL DEFAULT 0')
        con.commit()
        print("Column monthly_income added successfully.")
    except sqlite3.OperationalError:
        print("monthly_income column already exists or another error occurred.")

    con.close()

if __name__ == '__main__':
    update_db()  # Run this to update the database
