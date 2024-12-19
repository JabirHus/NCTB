import tkinter as tk
from tkinter import ttk
from gui.shared_components import show_frame

def create_account_page(root, account_frame, strategy_frame):
    """Set up the Account Page with dynamic slave accounts."""

    # Helper functions to reduce label and entry repetition
    def create_label(parent, text, font_size=12, fg="white", bg="#1C1C2E", **grid_options):
        """Create and grid a styled label."""
        return tk.Label(parent, text=text, font=("Helvetica", font_size), fg=fg, bg=bg).grid(**grid_options)

    def create_entry(parent, show=None, **grid_options):
        """Create and grid a styled entry."""
        return tk.Entry(parent, font=("Helvetica", 12), bg="#2C2C3E", fg="white", show=show, insertbackground="white").grid(**grid_options)

    # Configure the background
    account_frame.configure(bg="#1C1C2E")

    # Master Account Section
    tk.Label(account_frame, text="Master Account", font=("Helvetica", 16), fg="white", bg="#1C1C2E").pack(pady=(20, 10))
    master_frame = tk.Frame(account_frame, bg="#1C1C2E")
    master_frame.pack(pady=10)

    create_label(master_frame, "Username:", row=0, column=0, padx=10, pady=5, sticky="w")
    create_entry(master_frame, row=0, column=1, padx=10, pady=5)
    create_label(master_frame, "Password:", row=1, column=0, padx=10, pady=5, sticky="w")
    create_entry(master_frame, show="*", row=1, column=1, padx=10, pady=5)
    tk.Label(master_frame, text="Not connected", font=("Helvetica", 12), fg="red", bg="#1C1C2E").grid(
        row=0, column=2, rowspan=2, padx=10, sticky="e"
    )

    # Separator
    ttk.Separator(account_frame, orient="horizontal").pack(fill="x", padx=20, pady=20)

    # Slave Accounts Section
    tk.Label(account_frame, text="Slave Accounts", font=("Helvetica", 16), fg="white", bg="#1C1C2E").pack(pady=(0, 10))
    button_frame = tk.Frame(account_frame, bg="#1C1C2E")
    button_frame.pack()

    # Scrollable Slave Accounts Area
    border_frame = tk.Frame(account_frame, bg="#44475a", highlightthickness=2, highlightbackground="#44475a")
    border_frame.pack(padx=10, pady=10, fill="both", expand=True)
    canvas = tk.Canvas(border_frame, bg="#1C1C2E", highlightthickness=0)
    scrollbar = tk.Scrollbar(border_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#1C1C2E")

    canvas.create_window((0, 0), window=scrollable_frame, anchor="n")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Scrollwheel support
    def _on_mousewheel(event):
        canvas.yview_scroll(-1 * (event.delta // 120), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    rows_frame = tk.Frame(scrollable_frame, bg="#1C1C2E")
    rows_frame.pack(fill="both", expand=True)

    def add_slave_account():
        """Add a dynamic slave account section."""
        wrapper = tk.Frame(rows_frame, bg="#1C1C2E")
        wrapper.pack(fill="x", pady=5)

        slave_row = tk.Frame(wrapper, bg="#1C1C2E")
        slave_row.pack(pady=5, anchor="center")

        create_label(slave_row, "Username:", row=0, column=0, padx=5, pady=5, sticky="w")
        create_entry(slave_row, row=0, column=1, padx=5, pady=5)
        create_label(slave_row, "Password:", row=1, column=0, padx=5, pady=5, sticky="w")
        create_entry(slave_row, show="*", row=1, column=1, padx=5, pady=5)

        tk.Label(slave_row, text="Not connected", font=("Helvetica", 12), fg="red", bg="#1C1C2E").grid(
            row=0, column=2, rowspan=2, padx=10, sticky="e"
        )

        tk.Button(
            slave_row, text="Delete", bg="#1C1C2E", fg="white",
            activebackground="red", activeforeground="white",
            command=lambda: [wrapper.destroy(), canvas.configure(scrollregion=canvas.bbox("all"))]
        ).grid(row=0, column=3, rowspan=2, padx=10, pady=5)

    # Add Slave Account Button
    tk.Button(
        button_frame, 
        text="Add Slave Account", 
        bg="#1C1C2E", 
        fg="white",
        command=add_slave_account
    ).pack(pady=(5, 10))

    # Back Button
    tk.Button(
        button_frame, 
        text="Back", 
        bg="#1C1C2E", 
        fg="white",
        command=lambda: show_frame(strategy_frame)
    ).pack(pady=(0, 10))
