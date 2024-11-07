import sqlite3

def create_connection(db_file="trading_bot.db"):
    conn = sqlite3.connect(db_file)
    return conn

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

def insert_sample_trade():
    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trades (symbol, entry_price, exit_price, profit_loss)
        VALUES ('EURUSD', 1.1234, 1.1250, 10.5)
    """)
    conn.commit()
    conn.close()

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

# Call create_strategies_table() in main.py to ensure this table is created

def get_trade_history():
    """Fetch all rows from the trades table."""
    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades")
    rows = cursor.fetchall()
    conn.close()
    return rows