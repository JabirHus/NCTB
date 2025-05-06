
import tkinter as tk
from tkinter import ttk
from gui.shared_components import show_frame
from data.mt5_connector import connect_mt5
from data.account_storage import save_account, load_accounts, remove_account
from data.trade_copier import copy_master_trades
from data.strategy_executor import strategy_loop_for_all
import threading

executor_thread_started = False
copier_thread_started = False

trade_counter = {}
trade_count_updater = None
label_map = {}

# Register a callback to update trade counts dynamically on the GUI
def register_trade_count_updater(callback):
    global trade_count_updater
    trade_count_updater = callback

def update_trade_count(login, count):
    trade_counter[login] = count
    if login in label_map:
        label_info = label_map[login]
        label = label_info['label']
        balance = label_info['balance']
        equity = label_info['equity']
        new_text = (
            f"Account:   {login}     Balance:   {balance}     Equity:   {equity}     "
            f"Open Trades:   {count}     Status:   CONNECTED"
        )
        label.config(text=new_text)

def create_account_page(root, account_frame, strategy_frame):
    BG_COLOR = "#161B22"
    CARD_BG = "#21262D"
    TEXT_COLOR = "white"
    BUTTON_COLOR = "#30363D"
    GREEN_COLOR = "#2EA043"
    RED_COLOR = "#D73A49"

    account_frame.configure(bg=BG_COLOR)

    def log_to_gui(msg):
        log_text.insert(tk.END, msg + '\n')
        log_text.see(tk.END)

    # Launch strategy executor only once if a master account exists
    def start_strategy_executor_if_ready():
        global executor_thread_started
        accounts = load_accounts()
        masters = accounts["masters"]
        if not executor_thread_started and masters:
            executor_thread_started = True
            master = masters[0]
            thread = threading.Thread(
                target=lambda: strategy_loop_for_all(master["login"], master["password"], master["server"], logger=log_to_gui),
                daemon=True
            )
            thread.start()

    # Launch trade copier thread only once if both master and slave accounts exist
    def start_copier_if_ready():
        global copier_thread_started
        accounts = load_accounts()
        masters = accounts["masters"]
        slaves = accounts["slaves"]
        if not copier_thread_started and masters and slaves:
            copier_thread_started = True
            thread = threading.Thread(
                target=lambda: copy_master_trades(masters[0], slaves, logger=log_to_gui),
                daemon=True
            )
            thread.start()

    

    def monitor_manual_trades():
        import MetaTrader5 as mt5
        import time
        from datetime import datetime

        previous_tickets = set()
        logged_manuals = set()

        while True:
            accounts = load_accounts()
            masters = accounts.get("masters", [])
            if not masters:
                time.sleep(5)
                continue

            master = masters[0]
            if not mt5.initialize(login=int(master["login"]), password=master["password"], server=master["server"]):
                log_to_gui("[❌] Failed to initialize MT5 for manual trade monitor.")
                time.sleep(5)
                continue

            positions = mt5.positions_get()
            current_tickets = set()
            if positions:
                for pos in positions:
                    current_tickets.add(pos.ticket)

                    if not pos.comment.startswith("Trade-") and pos.ticket not in logged_manuals:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_to_gui(f"[{timestamp}] [🟢 Manual] Trade opened: {pos.symbol} {'BUY' if pos.type == 0 else 'SELL'} at {pos.price_open}")
                        logged_manuals.add(pos.ticket)
                        open_count = len(positions)
                        trade_counter[master["login"]] = open_count
                        update_trade_count(master["login"], open_count)

            closed_tickets = previous_tickets - current_tickets
            for closed_ticket in closed_tickets:
                if master["login"] in trade_counter:
                    trade_counter[master["login"]] = max(0, trade_counter[master["login"]] - 1)
                    update_trade_count(master["login"], trade_counter[master["login"]])
                    log_to_gui(f"[🔻] Trade closed: {closed_ticket} → Open count updated")

            previous_tickets = current_tickets
            time.sleep(4)
    def open_add_account_modal(is_master):
        modal = tk.Toplevel(account_frame)
        modal.title(f"Add {'Master' if is_master else 'Slave'} Account")
        modal.configure(bg=CARD_BG)
        modal.geometry("400x350")

        tk.Label(modal, text="Trading Platform*", fg=TEXT_COLOR, bg=CARD_BG).pack(pady=(10, 2), anchor="w", padx=20)
        platform_var = ttk.Combobox(modal, values=["MT4", "MT5"])
        platform_var.pack(pady=2, padx=20, fill="x")

        tk.Label(modal, text="Login*", fg=TEXT_COLOR, bg=CARD_BG).pack(pady=(10, 2), anchor="w", padx=20)
        login_entry = tk.Entry(modal, bg=BUTTON_COLOR, fg=TEXT_COLOR)
        login_entry.pack(pady=2, padx=20, fill="x")

        tk.Label(modal, text="Password*", fg=TEXT_COLOR, bg=CARD_BG).pack(pady=(10, 2), anchor="w", padx=20)
        password_entry = tk.Entry(modal, show="*", bg=BUTTON_COLOR, fg=TEXT_COLOR)
        password_entry.pack(pady=2, padx=20, fill="x")

        tk.Label(modal, text="Server*", fg=TEXT_COLOR, bg=CARD_BG).pack(pady=(10, 2), anchor="w", padx=20)
        server_entry = tk.Entry(modal, bg=BUTTON_COLOR, fg=TEXT_COLOR)
        server_entry.pack(pady=2, padx=20, fill="x")

        def submit_account():
            platform = platform_var.get()
            login = login_entry.get()
            password = password_entry.get()
            server = server_entry.get()

            if platform and login and password and server:
                if platform != "MT5":
                    tk.Label(modal, text="Only MT5 supported for now.", fg=RED_COLOR, bg=CARD_BG).pack(pady=5)
                    return
                success, result = connect_mt5(login, password, server)
                if success:
                    balance = f"{result['balance']:.2f} / {result['margin']:.2f}"
                    equity = f"{result['equity']:.2f}"
                    trades = f"{result['positions']}" if 'positions' in result else "0"
                    modal.destroy()
                    if is_master:
                        add_master_account(login, server, balance, equity, trades)
                    else:
                        add_slave_account(login, server, balance, equity, trades)
                    account_data = {
                        "login": login,
                        "password": password,
                        "server": server
                    }
                    save_account("masters" if is_master else "slaves", account_data)
                    start_copier_if_ready()
                else:
                    tk.Label(modal, text=f"Connection failed: {result}", fg=RED_COLOR, bg=CARD_BG).pack(pady=5)
            else:
                tk.Label(modal, text="All fields are required!", fg=RED_COLOR, bg=CARD_BG).pack(pady=5)

        tk.Button(modal, text="Add Account", command=submit_account, bg=GREEN_COLOR, fg=TEXT_COLOR).pack(pady=20)

    def create_tabs(parent):
        tab_frame = tk.Frame(parent, bg=CARD_BG)
        tab_frame.pack(fill="x", padx=20, pady=5)
        for tab_name in ["Accounts", "Open Positions", "Closed Positions"]:
            tk.Button(tab_frame, text=tab_name, font=("Helvetica", 12, "bold"),
                      bg=BUTTON_COLOR, fg=TEXT_COLOR, padx=20, pady=5, bd=0, relief="flat").pack(side="left", padx=10, pady=2)

    master_card = tk.Frame(account_frame, bg=CARD_BG, padx=15, pady=10, bd=2, relief="ridge")
    master_card.pack(pady=10, padx=20, fill="x")
    tk.Label(master_card, text="MASTERS", font=("Helvetica", 14, "bold"), fg=TEXT_COLOR, bg=CARD_BG).pack(anchor="w")
    create_tabs(master_card)
    master_container = tk.Frame(master_card, bg=CARD_BG)
    master_container.pack(fill="x")

    def add_master_account(login, server, balance, equity, trades):
        card = tk.Frame(master_container, bg=BUTTON_COLOR, padx=10, pady=10, bd=2, relief="ridge")
        card.pack(pady=5, padx=10, fill="x")
        text = (
            f"Account:   {login}     Balance:   {balance}     Equity:   {equity}     "
            f"Open Trades:   {trades}     Status:   CONNECTED"
        )
        label = tk.Label(card, text=text, fg=TEXT_COLOR, bg=BUTTON_COLOR, font=("Helvetica", 12, "bold"))
        label.pack(side="left", padx=10)
        label_map[login] = {"label": label, "balance": balance, "equity": equity}
        trade_counter[login] = int(trades)
        ttk.Checkbutton(card, variable=tk.BooleanVar(value=True)).pack(side="left", padx=5)
        tk.Button(card, text="Copy Settings", bg=GREEN_COLOR, fg=TEXT_COLOR, padx=5).pack(side="left", padx=5)
        tk.Button(card, text="🗑️", bg=RED_COLOR, fg=TEXT_COLOR, padx=5,
                  command=lambda: [card.destroy(), remove_account("masters", login)]).pack(side="left", padx=5)

    log_frame = tk.Frame(account_frame, bg=BG_COLOR)
    log_frame.pack(pady=10, padx=20, fill="both", expand=True)
    global log_text
    log_text = tk.Text(log_frame, height=10, bg="black", fg="lime", font=("Courier", 9), wrap="word")
    log_scrollbar = tk.Scrollbar(log_frame)
    log_text.config(yscrollcommand=log_scrollbar.set)
    log_scrollbar.config(command=log_text.yview)
    log_text.pack(side="left", fill="both", expand=True)
    log_scrollbar.pack(side="right", fill="y")

    slave_card = tk.Frame(account_frame, bg=CARD_BG, padx=15, pady=10, bd=2, relief="ridge")
    slave_card.pack(pady=10, padx=20, fill="x")
    tk.Label(slave_card, text="SLAVES", font=("Helvetica", 14, "bold"), fg=TEXT_COLOR, bg=CARD_BG).pack(anchor="w")
    create_tabs(slave_card)
    slave_container = tk.Frame(slave_card, bg=CARD_BG)
    slave_container.pack(fill="x")

    def add_slave_account(login, server, balance, equity, trades):
        card = tk.Frame(slave_container, bg=BUTTON_COLOR, padx=10, pady=10, bd=2, relief="ridge")
        card.pack(pady=5, padx=10, fill="x")
        text = (
            f"Account:   {login}     Balance:   {balance}     Equity:   {equity}     Open Trades:   {trades}     Status:   CONNECTED"
        )
        label = tk.Label(card, text=text, fg=TEXT_COLOR, bg=BUTTON_COLOR, font=("Helvetica", 12, "bold"))
        label.pack(side="left", padx=10)
        label_map[login] = {"label": label, "balance": balance, "equity": equity}
        trade_counter[login] = int(trades)
        ttk.Checkbutton(card, variable=tk.BooleanVar(value=True)).pack(side="left", padx=5)
        tk.Button(card, text="Copy Settings", bg=GREEN_COLOR, fg=TEXT_COLOR, padx=5).pack(side="left", padx=5)
        tk.Button(card, text="🗑️", bg=RED_COLOR, fg=TEXT_COLOR, padx=5,
                  command=lambda: [card.destroy(), remove_account("slaves", login)]).pack(side="left", padx=5)

    tk.Button(master_card, text="+ Add Master", bg=BUTTON_COLOR, fg=TEXT_COLOR,
              command=lambda: open_add_account_modal(True)).pack(pady=10)
    tk.Button(slave_card, text="+ Add Slave", bg=BUTTON_COLOR, fg=TEXT_COLOR,
              command=lambda: open_add_account_modal(False)).pack(pady=10)

    saved = load_accounts()
    for acc in saved["masters"]:
        success, result = connect_mt5(acc["login"], acc["password"], acc["server"])
        if success:
            balance = f"{result['balance']:.2f} / {result['margin']:.2f}"
            equity = f"{result['equity']:.2f}"
            trades = f"{result['positions']}" if 'positions' in result else "0"
            add_master_account(acc["login"], acc["server"], balance, equity, trades)
            start_copier_if_ready()
            start_strategy_executor_if_ready()

    for acc in saved["slaves"]:
        success, result = connect_mt5(acc["login"], acc["password"], acc["server"])
        if success:
            balance = f"{result['balance']:.2f} / {result['margin']:.2f}"
            equity = f"{result['equity']:.2f}"
            trades = f"{result['positions']}" if 'positions' in result else "0"
            add_slave_account(acc["login"], acc["server"], balance, equity, trades)
            start_copier_if_ready()

    tk.Button(
        account_frame,
        text="Back",
        bg=BUTTON_COLOR,
        fg=TEXT_COLOR,
        command=lambda: show_frame(strategy_frame)
    ).pack(pady=20)

    threading.Thread(target=monitor_manual_trades, daemon=True).start()
