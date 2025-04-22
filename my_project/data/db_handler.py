import duckdb

def create_connection(db_file="trading_bot.db"):
    return duckdb.connect(db_file)

def drop_trades_table():
    conn = create_connection()
    conn.execute("DROP TABLE IF EXISTS trades")
    conn.close()

def drop_strategies_table():
    conn = create_connection()
    conn.execute("DROP TABLE IF EXISTS strategies")
    conn.close()

def create_table():
    conn = create_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            symbol TEXT,
            entry_price REAL,
            exit_price REAL,
            profit_loss REAL,
            timestamp TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.close()

def create_strategies_table():
    conn = create_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            additional_indicators JSON
        )
    """)
    conn.close()

def insert_sample_trade():
    conn = create_connection()
    conn.execute("""
        INSERT INTO trades (symbol, entry_price, exit_price, profit_loss)
        VALUES ('EURUSD', 1.1234, 1.1250, 10.5)
    """)
    conn.close()
    print("Sample trade inserted successfully.")

def get_trade_history():
    conn = create_connection()
    rows = conn.execute("""
        SELECT 
            symbol, 
            ROUND(entry_price, 4) AS entry_price,
            ROUND(exit_price, 4) AS exit_price,
            ROUND(profit_loss, 2) AS profit_loss,
            STRFTIME(timestamp, '%Y-%m-%d %H:%M:%S') AS formatted_time
        FROM trades
    """).fetchall()
    conn.close()
    return rows

def clear_trade_history():
    conn = create_connection()
    conn.execute("DELETE FROM trades")
    conn.commit()
    conn.close()
    print("Trade history cleared.")