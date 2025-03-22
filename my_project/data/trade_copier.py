
import time
import MetaTrader5 as mt5
import json

# Track already copied master trades
try:
    with open("last_trades.json", "r") as f:
        last_trade_ids = set(json.load(f))
except FileNotFoundError:
    last_trade_ids = set()


def copy_master_trades(master, slaves):
    print("[Copier] Starting master-to-slave copier loop...")

    if not mt5.initialize(login=int(master["login"]), password=master["password"], server=master["server"]):
        print(f"[Copier ❌] Master initialization failed: {mt5.last_error()}")
        return False

    print(f"[Copier ✅] Master {master['login']} connected")

    # Preload open trades into memory
    positions = mt5.positions_get()
    if positions:
        for pos in positions:
            last_trade_ids.add(pos.ticket)

    print(f"[Copier] Skipping {len(last_trade_ids)} existing trades")

    while True:
        positions = mt5.positions_get()
        if positions:
            for pos in positions:
                ticket = pos.ticket
                if ticket in last_trade_ids:
                    continue

                print(f"[Copier] New master trade detected: {pos.symbol}, ticket {ticket}")
                
                successfully_copied = False

                for slave in slaves:
                    success = copy_trade_to_slave(slave, pos)
                    if success:
                        successfully_copied = True

                if successfully_copied:
                    last_trade_ids.add(ticket)

        # Save persistent state
        with open("last_trades.json", "w") as f:
            json.dump(list(last_trade_ids), f)

        time.sleep(2)


def copy_trade_to_slave(slave, pos):
    print(f"[Copier] Copying trade to slave {slave['login']}")

    mt5.shutdown()
    if not mt5.initialize(login=int(slave["login"]), password=slave["password"], server=slave["server"]):
        print(f"[Copier ❌] Failed to initialize slave {slave['login']}: {mt5.last_error()}")
        return False

    # ✅ Check if slave already has this trade (based on symbol and volume)
    slave_positions = mt5.positions_get(symbol=pos.symbol)
    if slave_positions:
        for p in slave_positions:
            if abs(p.volume - pos.volume) < 0.0001 and p.type == pos.type:
                print(f"[Copier 🔁] Trade already exists on slave {slave['login']}, skipping.")
                return False

    # Proceed to select and copy trade
    if not mt5.symbol_select(pos.symbol, True):
        print(f"[Copier ⚠️] Symbol {pos.symbol} not available on slave {slave['login']}")
        return False

    info = mt5.symbol_info(pos.symbol)
    if not info:
        print(f"[Copier ⚠️] No info for {pos.symbol} on slave {slave['login']}")
        return False

    step = info.volume_step
    min_vol = info.volume_min
    volume = max(min_vol, round(pos.volume / step) * step)
    volume = round(volume, 2)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": pos.symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY if pos.type == 0 else mt5.ORDER_TYPE_SELL,
        "price": pos.price_open,
        "deviation": 10,
        "magic": 234000,
        "comment": "Copied by Trade Copier",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    if pos.sl not in (None, 0.0):
        request["sl"] = pos.sl
    if pos.tp not in (None, 0.0):
        request["tp"] = pos.tp

    result = mt5.order_send(request)
    if result is None:
        print(f"[Copier ❌] order_send returned None for slave {slave['login']}. Likely an invalid request.")
        print(f"[Copier ⚠️] Full request: {request}")
        return False

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"[Copier ❌] Trade copy failed on slave {slave['login']} — {result.retcode}")
        return False
    else:
        print(f"[Copier ✅] Trade copied to slave {slave['login']} (ticket {result.order})")
        return True
