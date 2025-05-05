
import MetaTrader5 as mt5
import time
import json
import duckdb
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import threading
from data.db_handler import create_connection
import ctypes
# Prevent screen timeout
ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)
DB_PATH = "trading_bot.db"
STRATEGY_CHECK_INTERVAL = 10
open_trade_registry = {}
active_trades = set()
gui_logger = None
log_lock = threading.Lock()

def ensure_mt5_initialized(login, password, server):
    mt5.shutdown()
    return mt5.initialize(login=int(login), password=password, server=server)

symbols = [
    "GBPCHF+", "USDCAD+", "EURUSD+", "GBPUSD+", "NZDUSD+", "USDJPY+", "EURGBP+", "AUDUSD+"
]

symbol_locks = {s: threading.Lock() for s in symbols}

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {message}"
    with log_lock:
        print(full_msg)
        if gui_logger and ("[✅]" in message or "[🔁]" in message or "[🔄]" in message or "closed:" in message):
            gui_logger(full_msg)
        try:
            with open("trade_log.txt", "a", encoding="utf-8") as f:
                f.write(full_msg + "\n")
        except Exception as e:
            print(f"[Logger Error] {e}")

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
        results = {}
        all_signals = {}

        # Precompute all possible indicators only once
        try:
            if "RSI" in self.strategy and self.strategy["RSI"].get("var"):
                period = int(self.strategy["RSI"]["sub_indicators"]["Period"]["value"])
                df.ta.rsi(length=period, append=True)
        except Exception:
            pass
        try:
            df.ta.macd(append=True)
        except Exception:
            pass
        try:
            df.ta.bbands(append=True)
        except Exception:
            pass
        try:
            df.ta.stoch(append=True)
        except Exception:
            pass
        try:
            df.ta.sma(append=True)
        except Exception:
            pass

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

            results[ind] = dir if dir in ("BUY", "SELL") else None
            

        signals_str = ", ".join(f"{k}={v}" for k, v in results.items())
        directions = [v for v in results.values() if v]

        if len(directions) < len(results):
            log(f"[Multi-Indicator] {self.symbol} signals → {signals_str} → incomplete → skipping")
            return None

        if all(d == directions[0] for d in directions):
            log(f"[Multi-Indicator] {self.symbol} signals → {signals_str} → consensus: {directions[0]}")
            return directions[0]

        log(f"[Multi-Indicator] {self.symbol} signals → {signals_str} → conflict → skipping")
        return None





    def evaluate_rsi(self, df, config):
        period = int(config["sub_indicators"]["Period"]["value"])
        undersold = int(config["sub_indicators"]["Undersold"]["value"])
        oversold = int(config["sub_indicators"]["Oversold"]["value"])        
        rsi_val = df[f"RSI_{period}"].iloc[-1]
        log(f"[RSI Debug] {self.symbol} RSI={rsi_val:.2f} (Thresholds: <{undersold}=BUY, >{oversold}=SELL) → Suggestion: [{"BUY" if rsi_val < undersold else "SELL" if rsi_val > oversold else "NONE"}]")
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
        log(f"[MACD Debug] {self.symbol} MACD={macd:.5f}, Signal={signal_line:.5f} → [{'BUY' if macd > signal_line else 'SELL' if macd < signal_line else 'NO TRADE'}]")
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
        log(f"[Bollinger Debug] {self.symbol} Close={close:.5f}, Upper={upper:.5f}, Lower={lower:.5f}")
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
        log(f"[Stochastic Debug] {self.symbol} %K={k_val:.2f}")
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
        log(f"[SMA Debug] {self.symbol} Close={close:.5f}, SMA={ma_val:.5f} (Shift: {shift}) → Suggestion: [{"BUY" if close > ma_val else "SELL" if close < ma_val else "NONE"}]")
        if close > ma_val:
            return "BUY"
        elif close < ma_val:
            return "SELL"
        return None

def place_trade(symbol, volume=1, direction_str="BUY", master_login=None):
    with symbol_locks[symbol]:
        direction = mt5.ORDER_TYPE_BUY if direction_str == "BUY" else mt5.ORDER_TYPE_SELL

        if symbol in active_trades:
            log(f"[❌] Trade failed: {symbol} already active")
            return False

        tick = mt5.symbol_info_tick(symbol)
        info = mt5.symbol_info(symbol)

        if not info or not tick:
            log(f"[❌] Trade failed: Missing symbol info or tick for {symbol}")
            return False

        if not info.visible:
            if not mt5.symbol_select(symbol, True):
                log(f"[❌] Trade failed: Could not make {symbol} visible")
                return False

        digits = info.digits
        volume = max(info.volume_min, round(volume / info.volume_step) * info.volume_step)

        if volume <= 0:
            log(f"[❌] Trade failed: Invalid volume for {symbol}")
            return False

        price = tick.ask if direction == mt5.ORDER_TYPE_BUY else tick.bid
        if price is None or price <= 0:
            log(f"[❌] Trade failed: Invalid price for {symbol}")
            return False

        # Define pip sizes per symbol type
        if "JPY" in symbol:
            pip = 0.01
            sl_pips = 10   # 10 pips → 0.10
            tp_pips = 20
        elif symbol in ["BTCUSD", "ETHUSD"]:
            pip = 1.0      # 1 pip = $1
            sl_pips = 300  # 300 pips → $300
            tp_pips = 600
        else:
            pip = 0.0001
            sl_pips = 10   # 10 pips → 0.0010
            tp_pips = 20

        # Calculate SL/TP based on direction
        sl = price - sl_pips * pip if direction == mt5.ORDER_TYPE_BUY else price + sl_pips * pip
        tp = price + tp_pips * pip if direction == mt5.ORDER_TYPE_BUY else price - tp_pips * pip


        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": direction,
            "price": round(price, digits),
            "sl": round(sl, digits),
            "tp": round(tp, digits),
            "deviation": 10,
            "magic": 234001,
            "comment": f"Trade-{symbol}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            active_trades.add(symbol)
            try:
                from gui import account_page
                account_page.update_trade_count(master_login, len(mt5.positions_get() or []))
            except Exception as e:
                log(f"[TradeCounter] Update failed: {e}")
            return True

        log(f"[❌] Trade failed: {result.retcode if result else mt5.last_error()}")
        return False

def strategy_loop(master_login, master_password, master_server, symbol):
    if not ensure_mt5_initialized(master_login, master_password, master_server):
        log(f"[❌] MT5 Init failed for {symbol}: {mt5.last_error()}")
        return
    strategy = load_strategy_from_db()
    if not strategy:
        return
    evaluator = StrategyEvaluator(strategy, symbol)
    while True:
        df = get_symbol_data(symbol)
        if df is not None:
            direction = evaluator.evaluate(df)
            if direction and place_trade(symbol, direction_str=direction, master_login=master_login):
                log(f"[✅] {direction} trade placed on {symbol}")
        time.sleep(STRATEGY_CHECK_INTERVAL)

def reset_all_positions(master_login, master_password, master_server):
    if not ensure_mt5_initialized(master_login, master_password, master_server):
        log(f"[❌ Reset] MT5 Init failed for reset: {mt5.last_error()}")
        return

    positions = mt5.positions_get()
    if positions:
        for pos in positions:
            close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(pos.symbol).bid if close_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(pos.symbol).ask
            if not price or price <= 0:
                log(f"[Reset] Skipped invalid price for {pos.symbol}")
                continue

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": close_type,
                "position": pos.ticket,
                "price": price,
                "deviation": 10,
                "magic": 234001,
                "comment": "AutoResetClose",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC
            }

            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                log(f"[🔁 Reset] Closed position {pos.ticket} on {pos.symbol}")
                # Notify slave accounts via log update
                try:
                    with open("closed_master_trades.json", "r") as f:
                        closed_trades = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    closed_trades = []

                closed_trades.append({"ticket": pos.ticket, "symbol": pos.symbol})
                with open("closed_master_trades.json", "w") as f:
                    json.dump(closed_trades, f)

            else:
                log(f"[❌ Reset] Failed to close {pos.ticket} on {pos.symbol}: {mt5.last_error()}")

    active_trades.clear()
    open_trade_registry.clear()
    mt5.shutdown()
    log("[🔄 Reset] Cleared all internal trade records.")
    with open("last_trades.json", "w") as f:
        json.dump([], f)


def strategy_loop_for_all(master_login, master_password, master_server, logger=None):
    global gui_logger
    gui_logger = logger
    def periodic_reset():
        while True:
            log("[✅] 30 minute cycle begins now")
            time.sleep(1800)  # 30 mins
            reset_all_positions(master_login, master_password, master_server)
            time.sleep(2)
            log("[✅] 30 minute cycle ended. New cycle now")
            
    threading.Thread(target=periodic_reset, daemon=True).start()
    for symbol in symbols:
        threading.Thread(target=strategy_loop, args=(master_login, master_password, master_server, symbol), daemon=True).start()
        time.sleep(1)