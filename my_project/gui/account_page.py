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

    # Username Input
    tk.Label(master_frame, text="Username:", font=("Helvetica", 12), fg="white", bg="#1C1C2E").grid(
        row=0, column=0, padx=10, pady=5, sticky="w"
    )
    tk.Entry(master_frame, font=("Helvetica", 12), bg="#2C2C3E", fg="white", insertbackground="white").grid(
        row=0, column=1, padx=10, pady=5
    )

    # Password Input
    tk.Label(master_frame, text="Password:", font=("Helvetica", 12), fg="white", bg="#1C1C2E").grid(
        row=1, column=0, padx=10, pady=5, sticky="w"
    )
    tk.Entry(master_frame, font=("Helvetica", 12), bg="#2C2C3E", fg="white", show="*", insertbackground="white").grid(
        row=1, column=1, padx=10, pady=5
    )

    # Connection Status
    tk.Label(master_frame, text="Not connected", font=("Helvetica", 12), fg="red", bg="#1C1C2E").grid(
        row=0, column=2, rowspan=2, padx=10, sticky="e"
    )

    # Line Separator
    ttk.Separator(account_frame, orient="horizontal").pack(fill="x", padx=20, pady=20)

    # Slave Accounts Title
    tk.Label(
        account_frame, text="Slave Accounts", font=("Helvetica", 16), fg="white", bg="#1C1C2E"
    ).pack(pady=(0, 10))

    # Frame for Buttons (centered below the title)
    button_frame = tk.Frame(account_frame, bg="#1C1C2E")
    button_frame.pack()

    # Frame to contain the entire scrollable section with a border
    border_frame = tk.Frame(account_frame, bg="#44475a", highlightthickness=2, highlightbackground="#44475a")
    border_frame.pack(padx=10, pady=10, fill="both", expand=True)

    # Scrollable Frame for Slave Accounts
    canvas = tk.Canvas(border_frame, bg="#1C1C2E", highlightthickness=0)
    scrollbar = tk.Scrollbar(border_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#1C1C2E")

    # Configure scrolling
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="n")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Top Border Indicator (Static)
    top_border = tk.Frame(border_frame, bg="#44475a", height=3)
    top_border.place(relx=0, rely=0, relwidth=1)

    # Bottom Border Indicator (Static)
    bottom_border = tk.Frame(border_frame, bg="#44475a", height=3)
    bottom_border.place(relx=0, rely=1, relwidth=1, anchor="sw")


    # Enable Scrollwheel
    def _on_mousewheel(event):
        canvas.yview_scroll(-1 * (event.delta // 120), "units")

    # Bind scroll events for Windows/macOS
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # Bind scroll events for Linux
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    # Rows for slave accounts
    rows_frame = tk.Frame(scrollable_frame, bg="#1C1C2E")
    rows_frame.pack(fill="both", expand=True)

    def add_slave_account():
        """Add a dynamic slave account section."""
        # Wrap each row in a frame that will center its content
        slave_row_wrapper = tk.Frame(rows_frame, bg="#1C1C2E")
        slave_row_wrapper.pack(fill="x", pady=5)  # Frame to center content

        slave_row = tk.Frame(slave_row_wrapper, bg="#1C1C2E")
        slave_row.pack(pady=5, anchor="center")  # Centered inside the wrapper

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
            slave_row_wrapper.destroy()
            canvas.configure(scrollregion=canvas.bbox("all"))

        delete_button = tk.Button(
            slave_row,
            text="Delete",
            bg="#1C1C2E",
            fg="white",
            activebackground="red",
            activeforeground="white",
            command=delete_slave
        )
        delete_button.grid(row=0, column=3, rowspan=2, padx=10, pady=5)

    # Add Slave Account Button
    tk.Button(
        button_frame,
        text="Add Slave Account",
        font=("Helvetica", 12),
        bg="#1C1C2E",
        fg="white",
        activebackground="red",
        activeforeground="white",
        command=add_slave_account
    ).pack(pady=(5, 10))

    # Back Button
    tk.Button(
        button_frame,
        text="Back",
        font=("Helvetica", 12),
        bg="#1C1C2E",
        fg="white",
        activebackground="red",
        activeforeground="white",
        command=lambda: show_frame(strategy_frame)
    ).pack(pady=(0, 10))
