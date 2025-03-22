import time
import MetaTrader5 as mt5
from data.account_storage import load_accounts

def copy_master_trades(master, slaves):
    print("[Copier] Starting master-to-slave copier loop...")

    mt5.shutdown()
    if not mt5.initialize(login=int(master["login"]), password=master["password"], server=master["server"]):
        print(f"[Copier ❌] Master initialization failed: {mt5.last_error()}")
        return

    print(f"[Copier ✅] Master {master['login']} connected ✅")
    last_trade_ids = set()

    while True:
        positions = mt5.positions_get()

        if positions:
            for pos in positions:
                trade_id = pos.ticket
                symbol = pos.symbol
                volume = pos.volume
                action = "buy" if pos.type == 0 else "sell"
                price = pos.price_open

                if trade_id not in last_trade_ids:
                    print(f"[Copier] New master trade: ({trade_id}) {symbol} {action.upper()} {volume}")
                    last_trade_ids.add(trade_id)

                    for slave in slaves:
                        copy_trade_to_slave(slave, symbol, volume, price, action)

                    # Reconnect to Master
                    mt5.shutdown()
                    if not mt5.initialize(login=int(master["login"]), password=master["password"], server=master["server"]):
                        print(f"[Copier ❌] Failed to reconnect to Master after copying: {mt5.last_error()}")
                        return

        time.sleep(3)

def copy_trade_to_slave(slave, symbol, volume, price, action):
    mt5.shutdown()
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

    # Round volume to valid precision and step
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
