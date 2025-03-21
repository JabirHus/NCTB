import duckdb
import random
import time
from data.db_handler import create_connection
import json

class TradeExecutionEngine:
    def __init__(self):
        """Initialize the trade execution engine."""
        self.conn = create_connection()
        self.cursor = self.conn.cursor()

    def load_strategy(self):
        """Load the saved strategy from DuckDB."""
        self.cursor.execute("SELECT additional_indicators FROM strategies LIMIT 1")
        row = self.cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0])  # Convert JSON string to dictionary
        return None

    def generate_price(self):
        """Simulate market price fluctuations."""
        return round(random.uniform(1.1000, 1.2000), 4)  # Simulated EUR/USD prices

    def evaluate_trade_signal(self, strategy):
        """Decide whether to enter a trade based on the strategy rules."""
        price = self.generate_price()

        if "RSI" in strategy:
            rsi_threshold = int(strategy["RSI"]["sub_indicators"]["Undersold"]["value"])
            rsi_value = random.randint(10, 90)  # Simulated RSI value
            if rsi_value < rsi_threshold:
                return "BUY", price
            elif rsi_value > 100 - rsi_threshold:
                return "SELL", price

        if "MACD" in strategy:
            macd_fast = int(strategy["MACD"]["sub_indicators"]["Fast EMA"]["value"])
            macd_slow = int(strategy["MACD"]["sub_indicators"]["Slow EMA"]["value"])
            macd_value = random.uniform(-2.0, 2.0)  # Simulated MACD difference
            if macd_value > 0.5:
                return "BUY", price
            elif macd_value < -0.5:
                return "SELL", price

        return None, price  # No signal generated

    def execute_trade(self):
        """Execute a trade based on the strategy and log it in DuckDB."""
        strategy = self.load_strategy()
        if not strategy:
            print("No strategy found. Skipping trade execution.")
            return

        trade_action, entry_price = self.evaluate_trade_signal(strategy)
        if not trade_action:
            print("No valid trade signal generated.")
            return

        # Simulate exit price
        exit_price = entry_price + round(random.uniform(-0.0050, 0.0050), 4)
        profit_loss = round((exit_price - entry_price) * 10000, 2)  # Pips

        self.cursor.execute("SELECT MAX(id) FROM trades")
        max_id = self.cursor.fetchone()[0]
        next_id = 1 if max_id is None else max_id + 1

    
        # Log trade in DuckDB
        self.cursor.execute("""
            INSERT INTO trades (id, symbol, entry_price, exit_price, profit_loss, timestamp)
            VALUES (?, 'EUR/USD', ?, ?, ?, CURRENT_TIMESTAMP)
        """, (next_id, entry_price, exit_price, profit_loss))
        self.conn.commit()

        print(f"Trade Executed: {trade_action} @ {entry_price} -> Exit @ {exit_price} | P/L: {profit_loss} pips")

    def close(self):
        """Close the database connection."""
        self.conn.close()

# Example usage
if __name__ == "__main__":
    trade_engine = TradeExecutionEngine()
    while True:
        trade_engine.execute_trade()
        time.sleep(5)  # Execute trade every 5 seconds (simulated)
