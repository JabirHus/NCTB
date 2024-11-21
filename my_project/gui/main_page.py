# gui/main_page.py
import tkinter as tk
from gui.shared_components import show_frame, center_frame

def create_main_page(root, main_frame, history_frame, strategy_frame, populate_trade_history):
    """Set up the main intro page."""
    main_frame.configure(bg="#1C1C2E")

    # Use the centralized method to center the content
    center_frame(main_frame)

    # Create a content frame for widgets
    main_content = tk.Frame(main_frame, bg="#1C1C2E")
    main_content.grid(row=0, column=0)

    intro_label = tk.Label(
        main_content,
        text="The only: No Code Trading Bot + Trade Copier",
        font=("Helvetica", 18, "bold"),
        fg="white",
        bg="#1C1C2E"
    )
    intro_label.pack(pady=20)

    # "View Trade History" button configured to call populate_trade_history
    history_button = tk.Button(
        main_content,
        text="View Trade History",
        command=lambda: [populate_trade_history(), show_frame(history_frame)],  # Calls populate and navigates
        bg="#1C1C2E",
        fg="white"
    )
    history_button.pack(pady=10)

    strategy_button = tk.Button(
        main_content,
        text="Strategy Builder",
        command=lambda: show_frame(strategy_frame),
        bg="#1C1C2E",
        fg="white"
    )
    strategy_button.pack(pady=10)

    quit_button = tk.Button(main_content, text="Quit", command=root.destroy, bg="#1C1C2E", fg="white")
    quit_button.pack(pady=10)
