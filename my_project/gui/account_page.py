import tkinter as tk
from tkinter import ttk

def create_account_page(root, account_frame):
    """Set up the Account Page."""
    account_frame.configure(bg="white")  # Set background color

    # Master Account Section
    master_label = tk.Label(account_frame, text="Master Account", font=("Arial", 16, "bold"), bg="white")
    master_label.grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky="w")

    # Input fields for credentials
    username_label = tk.Label(account_frame, text="Username:", font=("Arial", 12), bg="white")
    username_label.grid(row=1, column=0, sticky="w", padx=10)
    username_entry = tk.Entry(account_frame, font=("Arial", 12))
    username_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

    password_label = tk.Label(account_frame, text="Password:", font=("Arial", 12), bg="white")
    password_label.grid(row=2, column=0, sticky="w", padx=10)
    password_entry = tk.Entry(account_frame, font=("Arial", 12), show="*")
    password_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

    # Connection status
    connection_status = tk.Label(account_frame, text="Not connected", font=("Arial", 12), fg="red", bg="white")
    connection_status.grid(row=1, column=2, rowspan=2, padx=(20, 10), sticky="e")

    # Horizontal separator
    separator = ttk.Separator(account_frame, orient="horizontal")
    separator.grid(row=3, column=0, columnspan=3, pady=20, sticky="ew", padx=10)

    # Add Slave Account Button
    add_slave_button = tk.Button(account_frame, text="Add Slave Account", font=("Arial", 12, "bold"), bg="lightgray", padx=10, pady=5)
    add_slave_button.grid(row=4, column=0, columnspan=3, pady=(10, 20))
