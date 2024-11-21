import duckdb

def create_connection(db_file="trading_bot.db"):
    conn = duckdb.connect(db_file)
    return conn

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY,  -- Define as PRIMARY KEY without auto-increment
            symbol TEXT,
            entry_price REAL,
            exit_price REAL,
            profit_loss REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.close()

def insert_sample_trade():
    conn = create_connection()
    cursor = conn.cursor()

    # Determine the next ID value
    cursor.execute("SELECT MAX(id) FROM trades")
    max_id = cursor.fetchone()[0]
    next_id = 1 if max_id is None else max_id + 1

    # Insert the trade with the calculated ID
    cursor.execute("""
        INSERT INTO trades (id, symbol, entry_price, exit_price, profit_loss)
        VALUES (?, ?, ?, ?, ?)
    """, (next_id, 'EURUSD', 1.1234, 1.1250, 10.5))

    conn.close()
    print(f"Sample trade inserted successfully with ID: {next_id}")

def create_strategies_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            rsi_selected INTEGER,
            macd_selected INTEGER,
            rsi_threshold REAL,
            macd_threshold REAL,
            additional_indicators JSON
        )
    """)
    conn.close()

def get_trade_history():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades")
    rows = cursor.fetchall()
    conn.close()
    return rows
