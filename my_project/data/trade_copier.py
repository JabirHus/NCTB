import time
import MetaTrader5 as mt5
from data.account_storage import load_accounts
import json

last_trade_ids = set()

try:
    with open("last_trades.json", "r") as f:
        last_trade_ids = set(json.load(f))
except FileNotFoundError:
    last_trade_ids = set()

def copy_master_trades(master, slaves):
    print("[Copier] Starting master-to-slave copier loop...")

    if not mt5.initialize(login=int(master["login"]), password=master["password"], server=master["server"]):
        print(f"[Copier ❌] Master initialization failed: {mt5.last_error()}")
        return

    print(f"[Copier ✅] Master {master['login']} connected")

    # Preload existing trades so they’re not copied again
    current_positions = mt5.positions_get()
    if current_positions:
        for pos in current_positions:
            last_trade_ids.add(pos.ticket)

    print(f"[Copier] Skipping {len(last_trade_ids)} existing master trade(s)")

    while True:
        positions = mt5.positions_get()

        new_trades = []

        if positions:
            for pos in positions:
                trade_id = pos.ticket
                if trade_id in last_trade_ids:
                    continue

                last_trade_ids.add(trade_id)
                new_trades.append(pos)

        if new_trades:
            print(f"[Copier] Detected {len(new_trades)} new trade(s)")
            for pos in new_trades:
                print(f"[Copier] Copying: ({pos.ticket}) {pos.symbol} {'BUY' if pos.type == 0 else 'SELL'} {pos.volume}")
                for slave in slaves:
                    copy_trade_to_slave(slave, pos.symbol, pos.volume, pos.price_open, "buy" if pos.type == 0 else "sell")

        # ✅ Save last trade IDs to disk (optional)
        with open("last_trades.json", "w") as f:
            json.dump(list(last_trade_ids), f)

        time.sleep(2)  # global loop pause, NOT per-trade


def copy_trade_to_slave(slave, symbol, volume, price, action):
    if not mt5.initialize(login=int(slave["login"]), password=slave["password"], server=slave["server"]):
        print(f"[Copier ❌] Slave {slave['login']} failed to connect: {mt5.last_error()}")
        return

    if not mt5.symbol_select(symbol, True):
        print(f"[Copier ⚠️] Symbol {symbol} not found/available on slave {slave['login']}")
        return

    info = mt5.symbol_info(symbol)
    if not info:
        print(f"[Copier ⚠️] Could not get symbol info for {symbol} on slave {slave['login']}")
        return

    step = info.volume_step
    min_vol = info.volume_min
    fixed_volume = max(min_vol, round(volume / step) * step)
    fixed_volume = round(fixed_volume, 2)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": fixed_volume,
        "type": mt5.ORDER_TYPE_BUY if action == "buy" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "deviation": 10,
        "magic": 123456,
        "comment": "Copied by Trade Copier",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"[Copier ❌] Failed for slave {slave['login']} — retcode: {result.retcode}, message: {result.comment}")
    else:
        print(f"[Copier ✅] Trade copied to slave {slave['login']} (ticket {result.order})")

    # 🚨 Optional: shutdown if you want a clean reset per loop, but not ideal for performance
    mt5.shutdown()
