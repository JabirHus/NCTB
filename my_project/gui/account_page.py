import tkinter as tk
from tkinter import ttk
from gui.shared_components import show_frame
from data.mt5_connector import connect_mt5
from data.account_storage import save_account, load_accounts, remove_account
from data.trade_copier import copy_master_trades
import threading

copier_thread_started = False  # Keeps copier from starting twice


def create_account_page(root, account_frame, strategy_frame):
    """Account Page with correct new slave/master values, ticked checkboxes, and buttons for slaves."""

    def start_copier_if_ready():
        global copier_thread_started
        accounts = load_accounts()
        masters = accounts["masters"]
        slaves = accounts["slaves"]

        if not copier_thread_started and masters and slaves:
            copier_thread_started = True
            print("[Copier] Starting copier in background thread...")

            thread = threading.Thread(
                target=lambda: copy_master_trades(masters[0], slaves),
                daemon=True
            )
            thread.start()


    # Color Palette
    BG_COLOR = "#161B22"
    CARD_BG = "#21262D"
    TEXT_COLOR = "white"
    BUTTON_COLOR = "#30363D"
    GREEN_COLOR = "#2EA043"
    RED_COLOR = "#D73A49"

    account_frame.configure(bg=BG_COLOR)

    # === Function to Open "Add Account" Modal ===
    def open_add_account_modal(is_master):
        """Popup for adding Master or Slave accounts."""
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

                    # Save account to storage
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

        # Validation error messages show above this line if needed
        tk.Button(
            modal,
            text="Add Account",
            command=submit_account,
            bg=GREEN_COLOR,
            fg=TEXT_COLOR
        ).pack(pady=20)



    # === Function to Create Tabs ===
    def create_tabs(parent):
        """Creates tab navigation for Masters/Slaves."""
        tab_frame = tk.Frame(parent, bg=CARD_BG)
        tab_frame.pack(fill="x", padx=20, pady=5)

        for tab_name in ["Accounts", "Open Positions", "Closed Positions"]:
            tab_button = tk.Button(tab_frame, text=tab_name, font=("Helvetica", 12, "bold"),
                                   bg=BUTTON_COLOR, fg=TEXT_COLOR, padx=20, pady=5, bd=0, relief="flat")
            tab_button.pack(side="left", padx=10, pady=2)

    # === Master Accounts Section ===
    master_card = tk.Frame(account_frame, bg=CARD_BG, padx=15, pady=10, bd=2, relief="ridge")
    master_card.pack(pady=10, padx=20, fill="x")

    tk.Label(master_card, text="MASTERS", font=("Helvetica", 14, "bold"), fg=TEXT_COLOR, bg=CARD_BG).pack(anchor="w")

    create_tabs(master_card)

    master_container = tk.Frame(master_card, bg=CARD_BG)
    master_container.pack(fill="x")

    def add_master_account(login, server, balance, equity, trades):
        """Dynamically add Master accounts (Correct Placeholder Values & Ticked Checkbox)."""
        card = tk.Frame(master_container, bg=BUTTON_COLOR, padx=10, pady=10, bd=2, relief="ridge")
        card.pack(pady=5, padx=10, fill="x")

        text = (
            f"Account:   {login}     Balance:   {balance}     Equity:   {equity}     "
            f"Open Trades:   {trades}     Status:   CONNECTED"
        )
        tk.Label(card, text=text, fg=TEXT_COLOR, bg=BUTTON_COLOR, font=("Helvetica", 12, "bold")).pack(side="left", padx=10)

        switch_var = tk.BooleanVar(value=True)  # Default Ticked
        ttk.Checkbutton(card, variable=switch_var).pack(side="left", padx=5)

        tk.Button(card, text="Copy Settings", bg=GREEN_COLOR, fg=TEXT_COLOR, padx=5).pack(side="left", padx=5)
        tk.Button(
            card, text="🗑️", bg=RED_COLOR, fg=TEXT_COLOR, padx=5,
            command=lambda: [card.destroy(), remove_account("masters", login)]
        ).pack(side="left", padx=5)


    # === Slave Accounts Section ===
    slave_card = tk.Frame(account_frame, bg=CARD_BG, padx=15, pady=10, bd=2, relief="ridge")
    slave_card.pack(pady=10, padx=20, fill="x")

    tk.Label(slave_card, text="SLAVES", font=("Helvetica", 14, "bold"), fg=TEXT_COLOR, bg=CARD_BG).pack(anchor="w")

    create_tabs(slave_card)

    slave_container = tk.Frame(slave_card, bg=CARD_BG)
    slave_container.pack(fill="x")

    def add_slave_account(login, server, balance, equity, trades):
        """Dynamically add Slave accounts (Correct Placeholder Values & Ticked Checkbox)."""
        card = tk.Frame(slave_container, bg=BUTTON_COLOR, padx=10, pady=10, bd=2, relief="ridge")
        card.pack(pady=5, padx=10, fill="x")

        text = (
            f"Account:   {login}     Balance:   {balance}     Equity:   {equity}     Open Trades:   {trades}     Status:   CONNECTED"
        )
        tk.Label(card, text=text, fg=TEXT_COLOR, bg=BUTTON_COLOR, font=("Helvetica", 12, "bold")).pack(side="left", padx=10)

        switch_var = tk.BooleanVar(value=True)  # Default Ticked
        ttk.Checkbutton(card, variable=switch_var).pack(side="left", padx=5)

        tk.Button(card, text="Copy Settings", bg=GREEN_COLOR, fg=TEXT_COLOR, padx=5).pack(side="left", padx=5)
        tk.Button(
            card, text="🗑️", bg=RED_COLOR, fg=TEXT_COLOR, padx=5,
            command=lambda: [card.destroy(), remove_account("slaves", login)]
        ).pack(side="left", padx=5)


    # Add Master & Slave Buttons (Inside Box)
    tk.Button(master_card, text="+ Add Master", bg=BUTTON_COLOR, fg=TEXT_COLOR, command=lambda: open_add_account_modal(True)).pack(pady=10)
    tk.Button(slave_card, text="+ Add Slave", bg=BUTTON_COLOR, fg=TEXT_COLOR, command=lambda: open_add_account_modal(False)).pack(pady=10)

    # Auto-load saved accounts
    saved = load_accounts()

    for acc in saved["masters"]:
        success, result = connect_mt5(acc["login"], acc["password"], acc["server"])
        if success:
            balance = f"{result['balance']:.2f} / {result['margin']:.2f}"
            equity = f"{result['equity']:.2f}"
            trades = f"{result['positions']}" if 'positions' in result else "0"
            add_master_account(acc["login"], acc["server"], balance, equity, trades)
            start_copier_if_ready()

    for acc in saved["slaves"]:
        success, result = connect_mt5(acc["login"], acc["password"], acc["server"])
        if success:
            balance = f"{result['balance']:.2f} / {result['margin']:.2f}"
            equity = f"{result['equity']:.2f}"
            trades = f"{result['positions']}" if 'positions' in result else "0"
            add_slave_account(acc["login"], acc["server"], balance, equity, trades)
            start_copier_if_ready()

    # Back Button (to return to Strategy Page)
    tk.Button(
        account_frame,
        text="Back",
        bg=BUTTON_COLOR,
        fg=TEXT_COLOR,
        command=lambda: show_frame(strategy_frame)
    ).pack(pady=20)