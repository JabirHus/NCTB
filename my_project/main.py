import tkinter as tk
import sqlite3
from data.db_handler import create_table, insert_sample_trade, create_strategies_table, get_trade_history

# Ensure tables are created
create_table()
create_strategies_table()
insert_sample_trade()

# Function to save the selected strategy in the database
def save_strategy():
    rsi_selected = rsi_var.get()
    macd_selected = macd_var.get()
    rsi_threshold = rsi_entry.get()
    macd_threshold = macd_entry.get()

    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()

    # Clear existing strategy (assuming one strategy saved at a time)
    cursor.execute("DELETE FROM strategies")

    # Insert new strategy
    cursor.execute("""
        INSERT INTO strategies (rsi_selected, macd_selected, rsi_threshold, macd_threshold)
        VALUES (?, ?, ?, ?)
    """, (rsi_selected, macd_selected, rsi_threshold, macd_threshold))

    conn.commit()
    conn.close()

    print("Strategy saved!")

# Function to load the last saved strategy and display it on the page
def load_strategy():
    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM strategies ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        # Populate fields with loaded data
        rsi_var.set(row[1])
        macd_var.set(row[2])
        rsi_entry.delete(0, tk.END)
        rsi_entry.insert(0, row[3])
        macd_entry.delete(0, tk.END)
        macd_entry.insert(0, row[4])

# Function to switch frames
def show_frame(frame):
    frame.tkraise()

# Set up the main Tkinter window
root = tk.Tk()
root.title("Trading Bot and Trade Copier")
root.geometry("800x600")

# Create frames for different pages
main_frame = tk.Frame(root)
history_frame = tk.Frame(root)
strategy_frame = tk.Frame(root)

for frame in (main_frame, history_frame, strategy_frame):
    frame.grid(row=0, column=0, sticky='nsew')

# Main Page
label = tk.Label(main_frame, text="Welcome to the Trading Bot!")
label.pack(pady=20)
history_button = tk.Button(main_frame, text="View Trade History", command=lambda: show_frame(history_frame))
history_button.pack()
strategy_button = tk.Button(main_frame, text="Strategy Builder", command=lambda: [load_strategy(), show_frame(strategy_frame)])
strategy_button.pack()
quit_button = tk.Button(main_frame, text="Quit", command=root.destroy)
quit_button.pack()

# Trade History Page
history_label = tk.Label(history_frame, text="Trade History", font=('Helvetica', 16))
history_label.pack(pady=20)
history_text = tk.Text(history_frame, width=80, height=20)
history_text.pack()

def populate_trade_history():
    history_text.delete("1.0", tk.END)
    rows = get_trade_history()
    for row in rows:
        history_text.insert(tk.END, f"{row}\n")

history_button.config(command=lambda: [populate_trade_history(), show_frame(history_frame)])
back_button = tk.Button(history_frame, text="Back", command=lambda: show_frame(main_frame))
back_button.pack(pady=10)

# Strategy Builder Page
strategy_label = tk.Label(strategy_frame, text="Strategy Builder", font=('Helvetica', 16))
strategy_label.pack(pady=20)
indicator_label = tk.Label(strategy_frame, text="Select Indicators:")
indicator_label.pack()

# Indicator selection with checkboxes
rsi_var = tk.IntVar()
macd_var = tk.IntVar()

rsi_check = tk.Checkbutton(strategy_frame, text="RSI", variable=rsi_var)
rsi_check.pack()
macd_check = tk.Checkbutton(strategy_frame, text="MACD", variable=macd_var)
macd_check.pack()

# Entry fields for parameters
rsi_param_label = tk.Label(strategy_frame, text="RSI Threshold:")
rsi_param_label.pack()
rsi_entry = tk.Entry(strategy_frame)
rsi_entry.pack()

macd_param_label = tk.Label(strategy_frame, text="MACD Threshold:")
macd_param_label.pack()
macd_entry = tk.Entry(strategy_frame)
macd_entry.pack()

# Save button
save_button = tk.Button(strategy_frame, text="Save Strategy", command=save_strategy)
save_button.pack()

# Back button to return to the main page
back_button_strategy = tk.Button(strategy_frame, text="Back", command=lambda: show_frame(main_frame))
back_button_strategy.pack(pady=10)

# Set the main frame as the starting page
show_frame(main_frame)

# Run the Tkinter event loop
root.mainloop()
