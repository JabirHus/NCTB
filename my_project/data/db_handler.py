import sqlite3

def create_connection(db_file="trading_bot.db"):
    """Create a database connection to the SQLite database."""
    conn = sqlite3.connect(db_file)
    return conn

def create_table():
    """Create the trades table if it doesn't exist."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            entry_price REAL,
            exit_price REAL,
            profit_loss REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def insert_sample_trade():
    """Insert a sample trade into the trades table."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trades (symbol, entry_price, exit_price, profit_loss)
        VALUES ('EURUSD', 1.1234, 1.1250, 10.5)
    """)
    conn.commit()
    conn.close()


def view_table():
    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        print(row)
