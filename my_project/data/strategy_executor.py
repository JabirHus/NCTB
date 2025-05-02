
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
    "EURJPY", "EURGBP", "GBPNZD"
]

symbol_locks = {s: threading.Lock() for s in symbols}

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {message}"
    with log_lock:
        print(full_msg)
        if gui_logger:
            if "[✅]" in message or "closed:" in message:
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
    def __init__(self, strategy, symbol_name=""):
        self.strategy = strategy
        self.symbol = symbol_name

    def evaluate(self, df):
        directions = []
        for ind, config in self.strategy.items():
            if not config.get("var", 0):
                continue
            dir = None
            if ind == "RSI":
                dir = self.evaluate_rsi(df, config)
            elif ind == "MACD":
                dir = self.evaluate_macd(df, config)
            elif ind == "Bollinger Bands":
                dir = self.evaluate_bollinger(df, config)
            elif ind == "Stochastic Oscillator":
                dir = self.evaluate_stochastic(df, config)
            elif ind == "Moving Average":
                dir = self.evaluate_moving_average(df, config)

            if dir not in ("BUY", "SELL"):
                log(f"[Multi-Indicator] {ind} returned no signal → skipping")
                return None
            directions.append(dir)

        if all(d == directions[0] for d in directions):
            return directions[0]
        log(f"[Multi-Indicator] Conflict between indicators: {directions}")
        return None

    def evaluate_rsi(self, df, config):
        period = int(config["sub_indicators"]["Period"]["value"])
        undersold = int(config["sub_indicators"]["Undersold"]["value"])
        oversold = int(config["sub_indicators"]["Oversold"]["value"])
        df.ta.rsi(length=period, append=True)
        rsi_val = df[f"RSI_{period}"].iloc[-1]
        log(f"[RSI Debug] {self.symbol} RSI={rsi_val:.2f} (Thresholds: <{undersold}=BUY, >{oversold}=SELL)")
        if rsi_val < undersold:
            return "BUY"
        elif rsi_val > oversold:
            return "SELL"
        return None

    def evaluate_macd(self, df, config):
        fast = int(config["sub_indicators"]["Fast EMA"]["value"])
        slow = int(config["sub_indicators"]["Slow EMA"]["value"])
        signal = int(config["sub_indicators"]["MACD SMA"]["value"])
        df.ta.macd(fast=fast, slow=slow, signal=signal, append=True)
        macd = df[f"MACD_{fast}_{slow}_{signal}"].iloc[-1]
        signal_line = df[f"MACDs_{fast}_{slow}_{signal}"].iloc[-1]
        log(f"[MACD Debug] {self.symbol} MACD={macd:.5f}, Signal={signal_line:.5f} → {'BUY' if macd > signal_line else 'SELL' if macd < signal_line else 'NO TRADE'}")
        if macd > signal_line:
            return "BUY"
        elif macd < signal_line:
            return "SELL"
        return None

    def evaluate_bollinger(self, df, config):
        period = int(config["sub_indicators"]["Period"]["value"])
        deviation = int(config["sub_indicators"]["Deviation"]["value"])
        shift = int(config["sub_indicators"]["Shift"]["value"])
        df.ta.bbands(length=period, std=deviation, append=True)
        close = df["close"].iloc[-1]
        upper = df[f"BBU_{period}_{deviation}.0"].iloc[-1]
        lower = df[f"BBL_{period}_{deviation}.0"].iloc[-1]
        log(f"[BB Debug] {self.symbol} Close={close:.5f}, Upper={upper:.5f}, Lower={lower:.5f}")
        if close < lower:
            return "BUY"
        elif close > upper:
            return "SELL"
        return None

    def evaluate_stochastic(self, df, config):
        k = int(config["sub_indicators"]["%K Period"]["value"])
        d = int(config["sub_indicators"]["%D Period"]["value"])
        s = int(config["sub_indicators"]["Slowing"]["value"])
        df.ta.stoch(k=k, d=d, smooth_k=s, append=True)
        k_val = df[f"STOCHk_{k}_{d}_{s}"].iloc[-1]
        d_val = df[f"STOCHd_{k}_{d}_{s}"].iloc[-1]
        log(f"[Stoch Debug] {self.symbol} %K={k_val:.2f}, %D={d_val:.2f} → {'BUY' if k_val < 20 else 'SELL' if k_val > 80 else 'NO TRADE'}")
        if k_val < 20:
            return "BUY"
        elif k_val > 80:
            return "SELL"
        return None

    def evaluate_moving_average(self, df, config):
        period = int(config["sub_indicators"]["Period"]["value"])
        shift = int(config["sub_indicators"]["Shift"]["value"])
        df.ta.sma(length=period, append=True)
        close = df["close"].iloc[-1]
        ma_val = df[f"SMA_{period}"].iloc[-(1 + shift)]
        log(f"[MA Debug] {self.symbol} Close={close:.5f}, SMA({period})={ma_val:.5f} → {'BUY' if close > ma_val else 'SELL' if close < ma_val else 'NO TRADE'}")
        if close > ma_val:
            return "BUY"
        elif close < ma_val:
            return "SELL"
        return None

def place_trade(symbol, volume=0.1, direction_str="BUY", master_login=None):
    with symbol_locks[symbol]:
        direction = mt5.ORDER_TYPE_BUY if direction_str == "BUY" else mt5.ORDER_TYPE_SELL

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
        price = tick.ask if direction == mt5.ORDER_TYPE_BUY else tick.bid

        if digits == 3:
            sl = price - 0.10 if direction == mt5.ORDER_TYPE_BUY else price + 0.10
            tp = price + 0.20 if direction == mt5.ORDER_TYPE_BUY else price - 0.20
        else:
            sl = price - 0.0010 if direction == mt5.ORDER_TYPE_BUY else price + 0.0010
            tp = price + 0.0020 if direction == mt5.ORDER_TYPE_BUY else price - 0.0020

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
            try:
                from gui.account_page import update_trade_count
                if master_login:
                    count = len(mt5.positions_get() or [])
                    update_trade_count(master_login, count)
            except Exception as e:
                print(f'[TradeCount] Failed to update master count: {e}')
            try:
                from gui.account_page import update_trade_count
                count = len(mt5.positions_get() or [])
                update_trade_count(symbol, count)
            except Exception as e:
                print(f'[TradeCount] Failed to update master trade count: {e}')
        try:
            from gui.account_page import trade_counter, update_trade_label
            trade_counter[symbol] = trade_counter.get(symbol, 0) + 1
            update_trade_label(symbol)
        except Exception as e:
            print(f'[TradeCounter] Error updating counter: {e}')
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

    evaluator = StrategyEvaluator(strategy, symbol)

    while True:
        df = get_symbol_data(symbol)
        if df is not None:
            direction = evaluator.evaluate(df)
            if direction and place_trade(symbol, direction_str=direction, master_login=master_login):
                log(f"[✅] {direction} trade placed on {symbol}")
        time.sleep(STRATEGY_CHECK_INTERVAL)