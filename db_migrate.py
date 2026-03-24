import sqlite3

def migrate():
    conn = sqlite3.connect('instance/outreach.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE businesses ADD COLUMN label VARCHAR(100);")
        print("Success: Added 'label' column to businesses table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'label' already exists.")
        else:
            print(f"Error: {e}")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate()
