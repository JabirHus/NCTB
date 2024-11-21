# gui/strategy_page.py
import tkinter as tk
from gui.shared_components import show_frame, center_frame
from data.db_handler import create_strategies_table

def create_strategy_page(root, strategy_frame, main_frame):
    """Set up the strategy builder page."""
    strategy_frame.configure(bg="#1C1C2E")

    # Use the centralized method to center the content
    center_frame(strategy_frame)

    # Create a content frame for widgets
    strategy_content = tk.Frame(strategy_frame, bg="#1C1C2E")
    strategy_content.grid(row=0, column=0)

    strategy_label = tk.Label(strategy_content, text="Strategy Builder", font=('Helvetica', 16), fg="white", bg="#1C1C2E")
    strategy_label.pack(pady=20)

    indicator_label = tk.Label(strategy_content, text="Select Indicators:", fg="white", bg="#1C1C2E")
    indicator_label.pack()

    # Variables for indicator selection
    rsi_var = tk.IntVar()
    macd_var = tk.IntVar()

    # Checkbox for RSI
    rsi_check = tk.Checkbutton(strategy_content, text="RSI", variable=rsi_var, bg="#1C1C2E", fg="white", selectcolor="#1C1C2E")
    rsi_check.pack()

    # Checkbox for MACD
    macd_check = tk.Checkbutton(strategy_content, text="MACD", variable=macd_var, bg="#1C1C2E", fg="white", selectcolor="#1C1C2E")
    macd_check.pack()

    # Entry fields for thresholds
    rsi_param_label = tk.Label(strategy_content, text="RSI Threshold:", fg="white", bg="#1C1C2E")
    rsi_param_label.pack()
    rsi_entry = tk.Entry(strategy_content)
    rsi_entry.pack()

    macd_param_label = tk.Label(strategy_content, text="MACD Threshold:", fg="white", bg="#1C1C2E")
    macd_param_label.pack()
    macd_entry = tk.Entry(strategy_content)
    macd_entry.pack()

    # Save strategy function
    def save_strategy():
        """Save the selected indicators and thresholds to the database."""
        rsi_selected = rsi_var.get()
        macd_selected = macd_var.get()
        rsi_threshold = rsi_entry.get()
        macd_threshold = macd_entry.get()

        # Save to the strategies table in the database
        from data.db_handler import create_connection
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM strategies")  # Clear old strategies
        cursor.execute("""
            INSERT INTO strategies (rsi_selected, macd_selected, rsi_threshold, macd_threshold)
            VALUES (?, ?, ?, ?)
        """, (rsi_selected, macd_selected, rsi_threshold, macd_threshold))
        conn.commit()
        conn.close()
        print("Strategy saved!")

    save_button = tk.Button(strategy_content, text="Save Strategy", command=save_strategy, bg="#1C1C2E", fg="white")
    save_button.pack(pady=10)

    # Button to return to the main page
    back_button_strategy = tk.Button(strategy_content, text="Back", command=lambda: show_frame(main_frame), bg="#1C1C2E", fg="white")
    back_button_strategy.pack(pady=10)

    # Load the saved strategy at startup
    def load_strategy():
        """Load the last saved strategy from the database."""
        from data.db_handler import create_connection
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM strategies ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            rsi_var.set(row[1])
            macd_var.set(row[2])
            rsi_entry.delete(0, tk.END)
            rsi_entry.insert(0, row[3])
            macd_entry.delete(0, tk.END)
            macd_entry.insert(0, row[4])

    load_strategy()
