# gui/strategy_page.py
import tkinter as tk
from tkinter import ttk
from gui.shared_components import show_frame, center_frame
import json
from data.db_handler import create_connection


def load_strategy(rsi_var, macd_var, rsi_entry, macd_entry, dynamic_frame, additional_indicators):
    """Load the last saved strategy from the database and populate the UI."""
    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Fetch the last strategy
        cursor.execute("SELECT * FROM strategies ORDER BY rowid DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            # Unpack the values
            rsi_selected, macd_selected, rsi_threshold, macd_threshold, additional_data = row

            # Update the UI fields
            rsi_var.set(rsi_selected)
            macd_var.set(macd_selected)

            rsi_entry.delete(0, tk.END)
            if rsi_threshold is not None:
                rsi_entry.insert(0, str(rsi_threshold))

            macd_entry.delete(0, tk.END)
            if macd_threshold is not None:
                macd_entry.insert(0, str(macd_threshold))

            # Update dynamically added indicators
            additional_data = json.loads(additional_data) if additional_data else {}
            for key, data in additional_data.items():
                if key not in additional_indicators:
                    add_indicator_to_ui(dynamic_frame, key, data.get("selected", 0), data.get("value", ""), additional_indicators)

            print("Strategy loaded successfully!")
        else:
            print("No strategies found in the database.")
    except Exception as e:
        print(f"Error loading strategy: {e}")


def add_indicator_to_ui(frame, indicator_name, is_selected, value, additional_indicators):
    """Add the selected indicator to the UI dynamically."""
    indicator_var = tk.IntVar(value=is_selected)
    sub_frame = tk.Frame(frame, bg="#1C1C2E")
    sub_frame.pack()

    indicator_check = tk.Checkbutton(
        sub_frame,
        text=f"{indicator_name}",
        variable=indicator_var,
        bg="#1C1C2E",
        fg="white",
        selectcolor="#1C1C2E"
    )
    indicator_check.pack(side="left")

    value_label = tk.Label(sub_frame, text="Value:", fg="white", bg="#1C1C2E")
    value_label.pack(side="left")

    value_entry = tk.Entry(sub_frame)
    value_entry.pack(side="left")
    value_entry.insert(0, value)

    additional_indicators[indicator_name] = {"var": indicator_var, "entry": value_entry}

    # Function to remove the indicator if unchecked
    def remove_indicator():
        if indicator_var.get() == 0:
            sub_frame.destroy()
            del additional_indicators[indicator_name]

    indicator_check.config(command=remove_indicator)


def create_strategy_page(root, strategy_frame, main_frame):
    """Set up the enhanced strategy builder page."""
    strategy_frame.configure(bg="#1C1C2E")

    # Use the centralized method to center the content
    center_frame(strategy_frame)

    # Create a content frame
    strategy_content = tk.Frame(strategy_frame, bg="#1C1C2E")
    strategy_content.grid(row=0, column=0)

    strategy_label = tk.Label(
        strategy_content, text="Strategy Builder", font=('Helvetica', 16), fg="white", bg="#1C1C2E"
    )
    strategy_label.pack(pady=20)

    indicator_label = tk.Label(strategy_content, text="Select Indicators:", fg="white", bg="#1C1C2E")
    indicator_label.pack()

    # Predefined indicators
    rsi_var = tk.IntVar()
    macd_var = tk.IntVar()
    additional_indicators = {}

    # Checkbox for RSI
    rsi_check = tk.Checkbutton(
        strategy_content, text="RSI", variable=rsi_var, bg="#1C1C2E", fg="white", selectcolor="#1C1C2E"
    )
    rsi_check.pack()

    # Entry field for RSI Threshold
    rsi_param_label = tk.Label(strategy_content, text="RSI Threshold:", fg="white", bg="#1C1C2E")
    rsi_param_label.pack()
    rsi_entry = tk.Entry(strategy_content)
    rsi_entry.pack()

    # Checkbox for MACD
    macd_check = tk.Checkbutton(
        strategy_content, text="MACD", variable=macd_var, bg="#1C1C2E", fg="white", selectcolor="#1C1C2E"
    )
    macd_check.pack()

    # Entry field for MACD Threshold
    macd_param_label = tk.Label(strategy_content, text="MACD Threshold:", fg="white", bg="#1C1C2E")
    macd_param_label.pack()
    macd_entry = tk.Entry(strategy_content)
    macd_entry.pack()

    # Dropdown menu for additional indicators
    indicators = ["Bollinger Bands", "Moving Average", "Stochastic Oscillator"]
    selected_indicator = tk.StringVar(value="Select an Indicator")

    dropdown = ttk.OptionMenu(strategy_content, selected_indicator, *indicators)
    dropdown.pack(pady=10)

    # Frame to hold dynamically added input fields
    dynamic_frame = tk.Frame(strategy_content, bg="#1C1C2E")
    dynamic_frame.pack()

    def add_indicator():
        indicator = selected_indicator.get()
        if indicator in indicators:
            indicators.remove(indicator)
            dropdown['menu'].delete(0, "end")
            for i in indicators:
                dropdown['menu'].add_command(label=i, command=lambda val=i: selected_indicator.set(val))
            add_indicator_to_ui(dynamic_frame, indicator, 1, "", additional_indicators)

    add_indicator_button = tk.Button(
        strategy_content, text="Add Indicator", command=add_indicator, bg="#1C1C2E", fg="white"
    )
    add_indicator_button.pack(pady=10)

    def save_strategy():
        print("Saving strategy...")  # Debug statement

        # Capture values from UI components
        rsi_selected = rsi_var.get()
        macd_selected = macd_var.get()
        rsi_threshold = rsi_entry.get() or None
        macd_threshold = macd_entry.get() or None

        # Collect additional indicators and their thresholds
        additional_data = {
            key: {"selected": indicator["var"].get(), "value": indicator["entry"].get()}
            for key, indicator in additional_indicators.items()
        }

        print(f"RSI Selected: {rsi_selected}")
        print(f"MACD Selected: {macd_selected}")
        print(f"RSI Threshold: {rsi_threshold}")
        print(f"MACD Threshold: {macd_threshold}")
        print(f"Additional Indicators: {additional_data}")

        try:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM strategies;")  # Remove previous strategy

            # Insert updated strategy
            cursor.execute("""
                INSERT INTO strategies (rsi_selected, macd_selected, rsi_threshold, macd_threshold, additional_indicators)
                VALUES (?, ?, ?, ?, ?)
            """, (rsi_selected, macd_selected, rsi_threshold, macd_threshold, json.dumps(additional_data)))

            conn.commit()
            print("Strategy saved successfully!")
        except Exception as e:
            print(f"Error saving strategy: {e}")
        finally:
            conn.close()

    save_button = tk.Button(
        strategy_content, text="Save Strategy", command=save_strategy, bg="#1C1C2E", fg="white"
    )
    save_button.pack(pady=10)

    back_button_strategy = tk.Button(
        strategy_content, text="Back", command=lambda: show_frame(main_frame), bg="#1C1C2E", fg="white"
    )
    back_button_strategy.pack(pady=10)

    load_strategy(rsi_var, macd_var, rsi_entry, macd_entry, dynamic_frame, additional_indicators)
