
import MetaTrader5 as mt5
import time
import json
import duckdb
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import threading
from data.db_handler import create_connection

DB_PATH = "trading_bot.db"
STRATEGY_CHECK_INTERVAL = 4
open_trade_registry = {}
active_trades = set()
gui_logger = None
log_lock = threading.Lock()

symbols = [
    "EURUSD", "USDCHF", "AUDUSD", "USDCAD",
    "EURJPY", "EURGBP"
]

symbol_locks = {s: threading.Lock() for s in symbols}

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {message}"
    with log_lock:
        print(full_msg)
        if gui_logger:
            gui_logger(full_msg)
        try:
            with open("trade_log.txt", "a", encoding="utf-8") as f:
                f.write(full_msg + "\n")
        except Exception as e:
            print(f"[Logger Error] Failed to write to log file: {e}")

def load_strategy_from_db():
    conn = duckdb.connect(DB_PATH)
    row = conn.execute("SELECT * FROM strategies LIMIT 1").fetchone()
    conn.close()
    if row and row[0]:
        return json.loads(row[0])
    return None

def get_symbol_data(symbol, timeframe=mt5.TIMEFRAME_M1, count=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df

class StrategyEvaluator:
    def __init__(self, strategy):
        self.strategy = strategy

    def evaluate(self, df):
        for ind, config in self.strategy.items():
            if not config.get("var", 0):
                continue
            if ind == "RSI" and not self.evaluate_rsi(df, config):
                return False
            if ind == "MACD" and not self.evaluate_macd(df, config):
                return False
        return True

    def evaluate_rsi(self, df, config):
        period = int(config["sub_indicators"]["Period"]["value"])
        undersold = int(config["sub_indicators"]["Undersold"]["value"])
        oversold = int(config["sub_indicators"]["Oversold"]["value"])
        df.ta.rsi(length=period, append=True)
        rsi_val = df[f"RSI_{period}"].iloc[-1]
        return rsi_val < undersold or rsi_val > oversold

    def evaluate_macd(self, df, config):
        fast = int(config["sub_indicators"]["Fast EMA"]["value"])
        slow = int(config["sub_indicators"]["Slow EMA"]["value"])
        signal = int(config["sub_indicators"]["MACD SMA"]["value"])
        df.ta.macd(fast=fast, slow=slow, signal=signal, append=True)
        macd = df[f"MACD_{fast}_{slow}_{signal}"].iloc[-1]
        signal_line = df[f"MACDs_{fast}_{slow}_{signal}"].iloc[-1]
        return macd > signal_line

def place_trade(symbol, volume=0.1):
    with symbol_locks[symbol]:
        direction = mt5.ORDER_TYPE_BUY

        if symbol in active_trades:
            return False

        tick = mt5.symbol_info_tick(symbol)
        info = mt5.symbol_info(symbol)
        if info is None:
            log(f"[❌] Failed to get symbol info for {symbol}")
            return False

        if not info.visible:
            if not mt5.symbol_select(symbol, True):
                log(f"[❌] Cannot select symbol {symbol}")
                return False

        digits = info.digits
        volume = max(info.volume_min, round(volume / info.volume_step) * info.volume_step)
        price = tick.ask

        if digits == 3:
            sl = price - 0.10
            tp = price + 0.20
        else:
            sl = price - 0.0010
            tp = price + 0.0020

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": direction,
            "price": price,
            "sl": round(sl, digits),
            "tp": round(tp, digits),
            "deviation": 10,
            "magic": 234001,
            "comment": f"Trade-{symbol}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result is None:
            log(f"[❌] order_send returned None for {symbol}. Error: {mt5.last_error()}")
            return False

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            active_trades.add(symbol)
            time.sleep(1.0)
            try:
                conn = create_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO trades (symbol, entry_price, exit_price, profit_loss) VALUES (?, ?, ?, ?)",
                    (symbol, price, 0.0, 0.0)
                )
                conn.close()
                #log(f"[LOG] Trade recorded in history: {symbol} @ {price}")
            except Exception as e:
                log(f"[❌ DB] Failed to log trade for {symbol}: {e}")
            return True
        else:
            log(f"[❌] Trade failed: {result.retcode}")
            return False


def strategy_loop_for_all(master_login, master_password, master_server, logger=None):
    global gui_logger
    gui_logger = logger

    if not mt5.initialize(login=int(master_login), password=master_password, server=master_server):
        log(f"[❌] MT5 Init failed: {mt5.last_error()}")
        return

    for symbol in symbols:
        threading.Thread(
            target=strategy_loop,
            args=(master_login, master_password, master_server, symbol),
            daemon=True
        ).start()
        time.sleep(1)


def strategy_loop(master_login, master_password, master_server, symbol="EURUSD"):
    if not mt5.initialize(login=int(master_login), password=master_password, server=master_server):
        log(f"[❌] MT5 Init failed: {mt5.last_error()}")
        return

    strategy = load_strategy_from_db()
    if not strategy or not isinstance(strategy, dict) or len(strategy) == 0:
        log(f"[⚠] No strategy for {symbol}")
        return

    evaluator = StrategyEvaluator(strategy)

    while True:
        df = get_symbol_data(symbol)
        if df is not None and evaluator.evaluate(df):
            if place_trade(symbol):
                log(f"[✅] Trade placed on {symbol}")
        time.sleep(STRATEGY_CHECK_INTERVAL)
