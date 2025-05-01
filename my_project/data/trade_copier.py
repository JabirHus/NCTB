
import MetaTrader5 as mt5
import time
import json
from datetime import datetime
import threading

log_lock = threading.Lock()

gui_logger = None

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {message}"
    with log_lock:
        print(full_msg)
    if gui_logger and ("trade copied" in message or "close on slave" in message):
        gui_logger(full_msg)
        try:
            with open("trade_log.txt", "a", encoding="utf-8") as f:
                f.write(full_msg + "\n")
        except Exception as e:
            print(f"[Logger Error] Failed to write to log file: {e}")

def copy_master_trades(master, slaves, logger=None):
    global gui_logger
    gui_logger = logger
    try:
        with open("last_trades.json", "r") as f:
            last_trade_ids = set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        last_trade_ids = set()

    copied_this_session = set(last_trade_ids)
    slave_trade_map = {}
    log("[Copier] Monitoring master account for new trades...")

    while True:
        time.sleep(1)

        if not mt5.initialize(login=int(master["login"]), password=master["password"], server=master["server"]):
            log(f"[❌ Copier] Failed to initialize master: {mt5.last_error()}")
            time.sleep(10)
            continue

        master_positions = mt5.positions_get()
        current_master_tickets = set(pos.ticket for pos in master_positions) if master_positions else set()
        new_copy_logs = []

        for pos in master_positions or []:
            ticket = pos.ticket
            if ticket in copied_this_session:
                continue

            for slave in slaves:
                if not mt5.initialize(login=int(slave["login"]), password=slave["password"], server=slave["server"]):
                    log(f"[❌ Copier] Failed to connect to slave {slave['login']}")
                    continue

                price = mt5.symbol_info_tick(pos.symbol).ask if pos.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(pos.symbol).bid

                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "type": pos.type,
                    "price": price,
                    "sl": pos.sl,
                    "tp": pos.tp,
                    "deviation": 10,
                    "magic": 123456,
                    "comment": f"Copy{ticket}",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC
                }

                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    new_copy_logs.append(f"[Copier] ✅ Trade copied to slave {slave['login']} (ticket {result.order})")
                    slave_trade_map.setdefault(ticket, {})[slave['login']] = {
                        "ticket": result.order,
                        "symbol": pos.symbol,
                        "volume": pos.volume,
                        "type": pos.type,
                        "comment": pos.comment
                    }

            copied_this_session.add(ticket)
            last_trade_ids.add(ticket)

        for msg in new_copy_logs:
            log(msg)

        closed_tickets = set(slave_trade_map.keys()) - current_master_tickets
        for ticket in closed_tickets:
            for slave in slaves:
                login = slave['login']
                slave_trade = slave_trade_map[ticket].get(login)
                if not slave_trade:
                    continue

                if not mt5.initialize(login=int(login), password=slave["password"], server=slave["server"]):
                    log(f"[❌ Copier] Failed to reconnect to slave {login} for closure")
                    continue

                close_price = mt5.symbol_info_tick(slave_trade["symbol"]).bid if slave_trade["type"] == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(slave_trade["symbol"]).ask
                close_request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": slave_trade["symbol"],
                    "volume": slave_trade["volume"],
                    "type": mt5.ORDER_TYPE_SELL if slave_trade["type"] == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                    "position": slave_trade["ticket"],
                    "price": close_price,
                    "deviation": 10,
                    "magic": 123456,
                    "comment": "AutoClose",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC
                }

                result = mt5.order_send(close_request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    reason = slave_trade.get("comment", "").lower()
                    if "tp" in reason:
                        icon = "✅ TP"
                    elif "sl" in reason:
                        icon = "🛑 SL"
                    else:
                        icon = "😊 Manual"
                    log(f"{icon} close on {slave_trade['symbol']} (ticket {slave_trade['ticket']}) [close on slave {login}]")
                else:
                    time.sleep(1)
                    retry_result = mt5.order_send(close_request)
                    if retry_result and retry_result.retcode == mt5.TRADE_RETCODE_DONE:
                        log(f"[Copier] 🔁 Retry succeeded: trade closed on slave {login} (ticket {slave_trade['ticket']})")
                    else:
                        code = retry_result.retcode if retry_result else result.retcode if result else 'N/A'
                        msg = mt5.last_error()
                        log(f"[❌ Copier] Failed to close trade {slave_trade['ticket']} on slave {login} after retry: ({code}, '{msg}')")

            slave_trade_map.pop(ticket, None)

        with open("last_trades.json", "w") as f:
            json.dump(list(last_trade_ids), f)

        time.sleep(1)
