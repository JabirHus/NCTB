import tkinter as tk
from data.db_handler import create_table, insert_sample_trade
import sqlite3

# Ensure the database table is created and insert sample data for testing
create_table()
insert_sample_trade()

# Function to retrieve trade history
def get_trade_history():
    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades")
    rows = cursor.fetchall()
    conn.close()
    return rows

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

# Main Page (Welcome Message)
label = tk.Label(main_frame, text="Welcome to the Trading Bot!")
label.pack(pady=20)

# Button to go to the Trade History page
history_button = tk.Button(main_frame, text="View Trade History", command=lambda: show_frame(history_frame))
history_button.pack()

# Button to go to the Strategy Builder page
strategy_button = tk.Button(main_frame, text="Strategy Builder", command=lambda: show_frame(strategy_frame))
strategy_button.pack()

# Quit button on the main page
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

# Indicator Selection
indicator_label = tk.Label(strategy_frame, text="Select Indicators:")
indicator_label.pack()

# Example indicators with checkboxes
rsi_var = tk.IntVar()
macd_var = tk.IntVar()

rsi_check = tk.Checkbutton(strategy_frame, text="RSI", variable=rsi_var)
rsi_check.pack()

macd_check = tk.Checkbutton(strategy_frame, text="MACD", variable=macd_var)
macd_check.pack()

# Parameters for indicators
rsi_param_label = tk.Label(strategy_frame, text="RSI Threshold:")
rsi_param_label.pack()
rsi_entry = tk.Entry(strategy_frame)
rsi_entry.pack()

macd_param_label = tk.Label(strategy_frame, text="MACD Threshold:")
macd_param_label.pack()
macd_entry = tk.Entry(strategy_frame)
macd_entry.pack()

# Save button (for now, it just prints the selected values)
def save_strategy():
    print("RSI Selected:", rsi_var.get())
    print("RSI Threshold:", rsi_entry.get())
    print("MACD Selected:", macd_var.get())
    print("MACD Threshold:", macd_entry.get())

save_button = tk.Button(strategy_frame, text="Save Strategy", command=save_strategy)
save_button.pack()

# Back button to go back to the main page
back_button_strategy = tk.Button(strategy_frame, text="Back", command=lambda: show_frame(main_frame))
back_button_strategy.pack(pady=10)

# Set the main frame as the starting page
show_frame(main_frame)

# Run the Tkinter event loop
root.mainloop()
