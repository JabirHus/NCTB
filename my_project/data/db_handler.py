import sqlite3

# Create a connection to the SQLite database (default file: trading_bot.db)
def create_connection(db_file="trading_bot.db"):
    conn = sqlite3.connect(db_file)
    return conn

# Create the 'trades' table if it does not already exist
def create_table():
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

# Insert a sample trade record into the 'trades' table
def insert_sample_trade():
    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trades (symbol, entry_price, exit_price, profit_loss)
        VALUES ('EURUSD', 1.1234, 1.1250, 10.5)
    """)
    conn.commit()
    conn.close()

# Create the 'strategies' table if it does not already exist
def create_strategies_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY,
            rsi_selected INTEGER,
            macd_selected INTEGER,
            rsi_threshold REAL,
            macd_threshold REAL
        )
    """)
    conn.commit()
    conn.close()

# Retrieve all rows from the 'trades' table
def get_trade_history():
    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades")
    rows = cursor.fetchall()
    conn.close()
    return rows
