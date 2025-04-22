import MetaTrader5 as mt5
import time
import json

def copy_master_trades(master, slaves):
    try:
        with open("last_trades.json", "r") as f:
            last_trade_ids = set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        last_trade_ids = set()

    print("[Copier] Monitoring master account for new trades...")

    while True:
        if not mt5.initialize(login=int(master["login"]), password=master["password"], server=master["server"]):
            print(f"[❌ Copier] Failed to initialize master: {mt5.last_error()}")
            time.sleep(10)
            continue

        master_positions = mt5.positions_get()
        if master_positions is None:
            print(f"[❌ Copier] Failed to get positions: {mt5.last_error()}")
            time.sleep(5)
            continue

        for pos in master_positions:
            ticket = pos.ticket
            if ticket not in last_trade_ids:
                for slave in slaves:
                    if not mt5.initialize(login=int(slave["login"]), password=slave["password"], server=slave["server"]):
                        print(f"[❌ Copier] Failed to connect to slave {slave['login']}")
                        continue

                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": pos.symbol,
                        "volume": pos.volume,
                        "type": pos.type,
                        "price": mt5.symbol_info_tick(pos.symbol).ask if pos.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(pos.symbol).bid,
                        "sl": pos.sl,
                        "tp": pos.tp,
                        "deviation": 10,
                        "magic": 123456,
                        "comment": f"Copy{ticket}",  # short safe comment
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC
                    }

                    result = mt5.order_send(request)
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        print(f"[Copier] ✅ Trade copied to slave {slave['login']} (ticket {result.order})")
                    else:
                        print(f"[❌ Copier] Failed to copy to slave {slave['login']}: {mt5.last_error()}")

        # Update JSON with new ticket(s)
        last_trade_ids.update([pos.ticket for pos in master_positions])
        with open("last_trades.json", "w") as f:
            json.dump(list(last_trade_ids), f)

        time.sleep(2.5)