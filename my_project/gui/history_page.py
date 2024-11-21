import tkinter as tk
from data.db_handler import get_trade_history
from gui.shared_components import show_frame, center_frame

def create_history_page(root, history_frame, main_frame):
    """Set up the trade history page."""
    history_frame.configure(bg="#1C1C2E")

    # Use the centralized method to center the content
    center_frame(history_frame)

    # Create a content frame for widgets
    history_content = tk.Frame(history_frame, bg="#1C1C2E")
    history_content.grid(row=0, column=0)

    history_label = tk.Label(
        history_content,
        text="Trade History",
        font=('Helvetica', 16),
        fg="white",
        bg="#1C1C2E"
    )
    history_label.pack(pady=20)

    # Text widget for trade history with calculated width
    history_text = tk.Text(
        history_content,
        width=84,  # Exact width to fit the longest line + 2 spaces
        height=20,
        bg="black",
        fg="white",
        wrap="none"  # Prevent text wrapping
    )
    history_text.configure(font=("Courier", 10))  # Monospace font for consistent alignment
    history_text.pack(pady=10)

    def populate_trade_history():
        """Fetch and display trade history with formatted output."""
        history_text.delete("1.0", tk.END)
        rows = get_trade_history()

        for row in rows:
            symbol = row[0]
            entry_price = row[1]  # Already rounded in SQL
            exit_price = row[2]   # Already rounded in SQL
            profit_loss = row[3]  # Already rounded in SQL
            timestamp = row[4]    # Formatted timestamp

            # Insert formatted data into the text widget
            history_text.insert(
                tk.END,
                f"Symbol: {symbol}, Entry: {entry_price:.4f}, Exit: {exit_price:.4f}, "
                f"P/L: {profit_loss:.2f}, Time: {timestamp}\n"
            )


    # Back button
    back_button = tk.Button(
        history_content,
        text="Back",
        command=lambda: show_frame(main_frame),
        bg="#1C1C2E",
        fg="white"
    )
    back_button.pack(pady=10)

    # Return the populate function for use in main.py
    return populate_trade_history
