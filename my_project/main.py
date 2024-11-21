# main.py
import tkinter as tk
from gui.shared_components import toggle_fullscreen, show_frame
from gui.main_page import create_main_page
from gui.history_page import create_history_page
from gui.strategy_page import create_strategy_page
from data.db_handler import create_table, create_strategies_table, insert_sample_trade

# Initialize database tables
create_table()
create_strategies_table()

# Insert a sample trade (test data)
insert_sample_trade()

# Set up the main Tkinter window
root = tk.Tk()
root.title("Trading Bot and Trade Copier")
root.geometry("800x600")
root.configure(bg="#1C1C2E")

root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

# Create frames for the app
main_frame = tk.Frame(root)
history_frame = tk.Frame(root)
strategy_frame = tk.Frame(root)

for frame in (main_frame, history_frame, strategy_frame):
    frame.grid(row=0, column=0, sticky="nsew")

# Set up pages
populate_trade_history = create_history_page(root, history_frame, main_frame)  # Get the populate function
create_main_page(root, main_frame, history_frame, strategy_frame, populate_trade_history)  # Pass it here
create_strategy_page(root, strategy_frame, main_frame)

# Fullscreen toggle binding
root.bind("<F11>", lambda event: toggle_fullscreen(root))

# Show the main frame initially
show_frame(main_frame)

# Start the Tkinter main loop
root.mainloop()
