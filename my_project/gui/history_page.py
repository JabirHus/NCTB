# gui/history_page.py
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

    history_label = tk.Label(history_content, text="Trade History", font=('Helvetica', 16), fg="white", bg="#1C1C2E")
    history_label.pack(pady=20)

    history_text = tk.Text(history_content, width=80, height=20, bg="black", fg="white")
    history_text.pack()

    def populate_trade_history():
        """Fetch and display trade history."""
        history_text.delete("1.0", tk.END)
        rows = get_trade_history()
        for row in rows:
            history_text.insert(tk.END, f"Symbol: {row[1]}, Entry: {row[2]}, Exit: {row[3]}, P/L: {row[4]}, Time: {row[5]}\n")

    # Button to return to the main page
    back_button = tk.Button(history_content, text="Back", command=lambda: show_frame(main_frame), bg="#1C1C2E", fg="white")
    back_button.pack(pady=10)

    # Return the populate function to be triggered when switching to this page
    return populate_trade_history
