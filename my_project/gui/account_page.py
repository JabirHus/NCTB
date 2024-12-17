import tkinter as tk
from tkinter import ttk
from gui.shared_components import show_frame

def create_account_page(root, account_frame, strategy_frame):
    """Set up the Account Page with dynamic slave accounts."""

    # Configure the background
    account_frame.configure(bg="#1C1C2E")

    # Master Account Section
    tk.Label(
        account_frame, text="Master Account", font=("Helvetica", 16), fg="white", bg="#1C1C2E"
    ).pack(pady=(20, 10))

    master_frame = tk.Frame(account_frame, bg="#1C1C2E")
    master_frame.pack(pady=10)

    tk.Label(master_frame, text="Username:", font=("Helvetica", 12), fg="white", bg="#1C1C2E").grid(
        row=0, column=0, padx=10, pady=5, sticky="w"
    )
    tk.Entry(master_frame, font=("Helvetica", 12), bg="#2C2C3E", fg="white", insertbackground="white").grid(
        row=0, column=1, padx=10, pady=5
    )

    tk.Label(master_frame, text="Password:", font=("Helvetica", 12), fg="white", bg="#1C1C2E").grid(
        row=1, column=0, padx=10, pady=5, sticky="w"
    )
    tk.Entry(master_frame, font=("Helvetica", 12), bg="#2C2C3E", fg="white", show="*", insertbackground="white").grid(
        row=1, column=1, padx=10, pady=5
    )

    tk.Label(master_frame, text="Not connected", font=("Helvetica", 12), fg="red", bg="#1C1C2E").grid(
        row=0, column=2, rowspan=2, padx=10, sticky="e"
    )

    # Line Separator
    ttk.Separator(account_frame, orient="horizontal").pack(fill="x", padx=20, pady=20)

    # Slave Accounts Title
    tk.Label(
        account_frame, text="Slave Accounts", font=("Helvetica", 16), fg="white", bg="#1C1C2E"
    ).pack(pady=(0, 10))

    slave_accounts_frame = tk.Frame(account_frame, bg="#1C1C2E")
    slave_accounts_frame.pack()

    def add_slave_account():
        """Add a dynamic slave account section."""
        slave_row = tk.Frame(slave_accounts_frame, bg="#1C1C2E")
        slave_row.pack(fill="x", pady=5, padx=10)

        # Username Input
        tk.Label(slave_row, text="Username:", font=("Helvetica", 12), fg="white", bg="#1C1C2E").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        tk.Entry(slave_row, font=("Helvetica", 12), bg="#2C2C3E", fg="white", insertbackground="white").grid(
            row=0, column=1, padx=5, pady=5
        )

        # Password Input
        tk.Label(slave_row, text="Password:", font=("Helvetica", 12), fg="white", bg="#1C1C2E").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        tk.Entry(slave_row, font=("Helvetica", 12), bg="#2C2C3E", fg="white", show="*", insertbackground="white").grid(
            row=1, column=1, padx=5, pady=5
        )

        # Connection Status
        tk.Label(slave_row, text="Not connected", font=("Helvetica", 12), fg="red", bg="#1C1C2E").grid(
            row=0, column=2, rowspan=2, padx=10, sticky="e"
        )

        # Delete Button
        def delete_slave():
            slave_row.destroy()

        def on_hover(event):
            delete_button.config(bg="red", fg="white")  # Red background on hover

        def on_leave(event):
            delete_button.config(bg="#1C1C2E", fg="white")  # Revert to default style

        delete_button = tk.Button(
            slave_row,
            text="Delete",
            bg="#1C1C2E",  # Default background
            fg="white",    # Default text color
            command=delete_slave
        )
        delete_button.grid(row=0, column=3, rowspan=2, padx=10, pady=5)

        # Bind hover events
        delete_button.bind("<Enter>", on_hover)
        delete_button.bind("<Leave>", on_leave)

    # Add Slave Account Button
    tk.Button(
        account_frame,
        text="Add Slave Account",
        bg="#1C1C2E",
        fg="white",
        command=add_slave_account
    ).pack(pady=10)

    # Back Button
    tk.Button(
        account_frame,
        text="Back",
        bg="#1C1C2E",
        fg="white",
        command=lambda: show_frame(strategy_frame)
    ).pack(pady=(10, 20))
