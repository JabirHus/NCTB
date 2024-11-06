import tkinter as tk
from data.db_handler import create_table  # Import create_table from db_handler.py

# Ensure the database table is created before anything else
create_table()

# Set up the main Tkinter window
root = tk.Tk()
root.title("Trading Bot and Trade Copier")
root.geometry("800x600")

# Example UI component
label = tk.Label(root, text="Welcome to the Trading Bot!")
label.pack()

# Run the Tkinter event loop
root.mainloop()
