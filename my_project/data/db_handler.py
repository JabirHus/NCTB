#db_handler.py
import duckdb

def create_connection(db_file="trading_bot.db"):
    conn = duckdb.connect(db_file)
    return conn

def drop_strategies_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS strategies")
    conn.close()


def create_table():
    """Create the trades table."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            entry_price REAL,  -- Floating-point number
            exit_price REAL,   -- Floating-point number
            profit_loss REAL,  -- Floating-point number
            timestamp TIMESTAMP DEFAULT NOW()  -- Automatically inserts current time
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
    """Create the strategies table with a unique primary key."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            additional_indicators JSON
        )
    """)
    conn.close()


def get_trade_history():
    """Fetch all rows from the trades table with built-in formatting."""
    conn = create_connection()
    cursor = conn.cursor()

    # Query with built-in rounding and timestamp formatting
    rows = cursor.execute("""
        SELECT 
            symbol, 
            ROUND(entry_price, 4) AS entry_price,  -- Round to 4 decimal places
            ROUND(exit_price, 4) AS exit_price,   -- Round to 4 decimal places
            ROUND(profit_loss, 2) AS profit_loss, -- Round to 2 decimal places
            STRFTIME(timestamp, '%Y-%m-%d %H:%M:%S') AS formatted_time -- Format timestamp
        FROM trades
    """).fetchall()

    conn.close()
    return rows


def clear_trade_history():
    """Delete all records from the trades table but keep the table structure."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trades")
    conn.commit()
    conn.close()
    print("Trade history cleared (table preserved).")
