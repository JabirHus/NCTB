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
    cursor.execute("DELETE FROM strategies")  # Clear previous strategy to save the new one
    cursor.execute("""
        INSERT INTO strategies (rsi_selected, macd_selected, rsi_threshold, macd_threshold)
        VALUES (?, ?, ?, ?)
    """, (rsi_selected, macd_selected, rsi_threshold, macd_threshold))
    conn.commit()
    conn.close()
    print("Strategy saved!")

# Function to load the last saved strategy and set it on the page
def load_strategy():
    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM strategies ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        # Set checkbox and entry field values based on loaded data
        rsi_var.set(row[1])
        macd_var.set(row[2])
        rsi_entry.delete(0, tk.END)
        rsi_entry.insert(0, row[3])
        macd_entry.delete(0, tk.END)
        macd_entry.insert(0, row[4])

def show_frame(frame):
    frame.tkraise()

# Set up the main Tkinter window
root = tk.Tk()
root.title("Trading Bot and Trade Copier")
root.geometry("800x600")
root.configure(bg="#1C1C2E")  # Space blue color for the window background

# Configure window resizing behavior
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

# Function to toggle fullscreen
def toggle_fullscreen(event=None):
    root.attributes("-fullscreen", not root.attributes("-fullscreen"))

# Bind the F11 key to toggle fullscreen
root.bind("<F11>", toggle_fullscreen)

# Create frames for different pages with background color
main_frame = tk.Frame(root, bg="#1C1C2E")
history_frame = tk.Frame(root, bg="#1C1C2E")
strategy_frame = tk.Frame(root, bg="#1C1C2E")

for frame in (main_frame, history_frame, strategy_frame):
    frame.grid(row=0, column=0, sticky="nsew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

# Centered content on Main Page
main_content = tk.Frame(main_frame, bg="#1C1C2E")
main_content.grid(row=0, column=0, sticky="nsew")

intro_label = tk.Label(
    main_content,
    text="The only: No Code Trading Bot + Trade Copier",
    font=("Helvetica", 18, "bold"),
    fg="white",
    bg="#1C1C2E"
)
intro_label.pack(pady=20)

history_button = tk.Button(main_content, text="View Trade History", command=lambda: show_frame(history_frame))
history_button.pack(pady=10)

strategy_button = tk.Button(main_content, text="Strategy Builder", command=lambda: show_frame(strategy_frame))
strategy_button.pack(pady=10)

quit_button = tk.Button(main_content, text="Quit", command=root.destroy)
quit_button.pack(pady=10)

# Centered content on Trade History Page
history_content = tk.Frame(history_frame, bg="#1C1C2E")
history_content.grid(row=0, column=0, sticky="nsew")

history_label = tk.Label(history_content, text="Trade History", font=('Helvetica', 16), fg="white", bg="#1C1C2E")
history_label.pack(pady=20)

history_text = tk.Text(history_content, width=80, height=20, bg="black", fg="white")
history_text.pack()

def populate_trade_history():
    history_text.delete("1.0", tk.END)
    rows = get_trade_history()
    for row in rows:
        history_text.insert(tk.END, f"{row}\n")

history_button.config(command=lambda: [populate_trade_history(), show_frame(history_frame)])
back_button = tk.Button(history_content, text="Back", command=lambda: show_frame(main_frame), bg="#1C1C2E", fg="white")
back_button.pack(pady=10)

# Centered content on Strategy Builder Page
strategy_content = tk.Frame(strategy_frame, bg="#1C1C2E")
strategy_content.grid(row=0, column=0, sticky="nsew")

strategy_label = tk.Label(strategy_content, text="Strategy Builder", font=('Helvetica', 16), fg="white", bg="#1C1C2E")
strategy_label.pack(pady=20)

indicator_label = tk.Label(strategy_content, text="Select Indicators:", fg="white", bg="#1C1C2E")
indicator_label.pack()

# Indicator selection with checkboxes
rsi_var = tk.IntVar()
macd_var = tk.IntVar()

rsi_check = tk.Checkbutton(strategy_content, text="RSI", variable=rsi_var, bg="#1C1C2E", fg="white", selectcolor="#1C1C2E")
rsi_check.pack()
macd_check = tk.Checkbutton(strategy_content, text="MACD", variable=macd_var, bg="#1C1C2E", fg="white", selectcolor="#1C1C2E")
macd_check.pack()

# Entry fields for parameters
rsi_param_label = tk.Label(strategy_content, text="RSI Threshold:", fg="white", bg="#1C1C2E")
rsi_param_label.pack()
rsi_entry = tk.Entry(strategy_content)
rsi_entry.pack()

macd_param_label = tk.Label(strategy_content, text="MACD Threshold:", fg="white", bg="#1C1C2E")
macd_param_label.pack()
macd_entry = tk.Entry(strategy_content)
macd_entry.pack()

save_button = tk.Button(strategy_content, text="Save Strategy", command=save_strategy, bg="#1C1C2E", fg="white")
save_button.pack(pady=10)

back_button_strategy = tk.Button(strategy_content, text="Back", command=lambda: show_frame(main_frame), bg="#1C1C2E", fg="white")
back_button_strategy.pack(pady=10)

# Load the saved strategy once at startup
load_strategy()

# Set the main frame as the starting page
show_frame(main_frame)

# Run the Tkinter event loop
root.mainloop()
