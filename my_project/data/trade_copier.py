import time
import MetaTrader5 as mt5
import json

# Track already copied master trades
try:
    with open("last_trades.json", "r") as f:
        last_trade_ids = set(json.load(f))
except FileNotFoundError:
    last_trade_ids = set()

# Track when trades were seen (to avoid immediate closure)
seen_timestamps = {}

def copy_master_trades(master, slaves):
    print("[Copier] Starting master-to-slave copier loop...")

    if not mt5.initialize(login=int(master["login"]), password=master["password"], server=master["server"]):
        print(f"[Copier ❌] Master initialization failed: {mt5.last_error()}")
        return False

    print(f"[Copier ✅] Master {master['login']} connected")

    # Load only this master’s trades
    positions = mt5.positions_get(login=int(master["login"]))
    if positions is None:
        positions = []

    for pos in positions:
        last_trade_ids.add(pos.ticket)

    print(f"[Copier] Skipping {len(last_trade_ids)} existing trades")

    previous_master_positions = {p.ticket: p for p in positions}

    while True:

        mt5.shutdown()
        if not mt5.initialize(login=int(master["login"]), password=master["password"], server=master["server"]):
            print(f"[Copier ❌] Failed to reinitialize master {master['login']} in loop: {mt5.last_error()}")
            continue


        positions = mt5.positions_get(login=int(master["login"]))
        if positions is None:
            positions = []

        current_master_positions = {p.ticket: p for p in positions}

        # === Detect new trades ===
        for ticket, pos in current_master_positions.items():
            if ticket not in last_trade_ids:
                print(f"[Copier] New master trade detected: {pos.symbol}, ticket {ticket}")
                seen_timestamps[ticket] = time.time()

                successfully_copied = False
                for slave in slaves:
                    success = copy_trade_to_slave(slave, pos)
                    if success:
                        successfully_copied = True

                if successfully_copied:
                    last_trade_ids.add(ticket)

        # === Detect closed trades ===
        closed_tickets = set(previous_master_positions.keys()) - set(current_master_positions.keys())
        for ticket in closed_tickets:
            if time.time() - seen_timestamps.get(ticket, 0) < 3:
                print(f"[Copier ⏳] Skipping closure for {ticket} — just copied.")
                continue

            closed_pos = previous_master_positions[ticket]
            print(f"[Copier 🔒] Master trade closed: {closed_pos.symbol}, ticket {ticket}")
            for slave in slaves:
                close_slave_trade(slave, ticket, closed_pos.symbol, closed_pos.type, closed_pos.volume)
            last_trade_ids.discard(ticket)

        # Save persistent state
        with open("last_trades.json", "w") as f:
            json.dump(list(last_trade_ids), f)

        previous_master_positions = current_master_positions
        time.sleep(2)



def copy_trade_to_slave(slave, pos):
    print(f"[Copier] Copying trade to slave {slave['login']}")

    mt5.shutdown()
    if not mt5.initialize(login=int(slave["login"]), password=slave["password"], server=slave["server"]):
        print(f"[Copier ❌] Failed to initialize slave {slave['login']}: {mt5.last_error()}")
        return False

    slave_positions = mt5.positions_get(symbol=pos.symbol)
    if slave_positions:
        for p in slave_positions:
            if abs(p.volume - pos.volume) < 0.0001 and p.type == pos.type:
                print(f"[Copier 🔁] Trade already exists on slave {slave['login']}, skipping.")
                return False

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
        "type": mt5.ORDER_TYPE_BUY if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_SELL,
        "price": mt5.symbol_info_tick(pos.symbol).ask if pos.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(pos.symbol).bid,
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

    print(f"[Copier ✅] Trade copied to slave {slave['login']} (ticket {result.order})")
    return True


def close_slave_trade(slave, closed_ticket, symbol, type_, volume):
    print(f"[Copier] Closing trade on slave {slave['login']} (symbol={symbol}, type={type_})")

    mt5.shutdown()
    if not mt5.initialize(login=int(slave["login"]), password=slave["password"], server=slave["server"]):
        print(f"[Copier ❌] Failed to initialize slave {slave['login']} for closing trade: {mt5.last_error()}")
        return False

    slave_positions = mt5.positions_get(symbol=symbol)
    if slave_positions:
        for p in slave_positions:
            if abs(p.volume - volume) < 0.0001 and p.type == type_:
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "position": p.ticket,
                    "symbol": p.symbol,
                    "volume": p.volume,
                    "type": mt5.ORDER_TYPE_SELL if p.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                    "price": mt5.symbol_info_tick(p.symbol).bid if p.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(p.symbol).ask,
                    "deviation": 10,
                    "magic": 234000,
                    "comment": "Closed by Trade Copier",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }

                result = mt5.order_send(request)
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"[Copier ✅] Closed slave trade on {slave['login']} (ticket {p.ticket})")
                    return True
                else:
                    print(f"[Copier ❌] Failed to close trade on {slave['login']} — {result.retcode}")
    return False