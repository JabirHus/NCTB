import tkinter as tk
from tkinter import ttk
from gui.shared_components import show_frame, center_frame
import json
from data.db_handler import create_connection


def update_dropdown_menu(dropdown, indicators, additional_indicators, selected_indicator):
    """Update the dropdown menu to show only unticked indicators."""
    dropdown['menu'].delete(0, "end")

    # Get unticked indicators (not in additional_indicators)
    unticked_indicators = [indicator for indicator in indicators if indicator not in additional_indicators]

    # Populate the dropdown with unticked indicators
    for indicator in unticked_indicators:
        dropdown['menu'].add_command(
            label=indicator,
            command=lambda val=indicator: selected_indicator.set(val)
        )


def add_indicator_to_ui(dynamic_frame, indicator, is_selected, value, additional_indicators, dropdown, indicators, selected_indicator):
    """Add an indicator dynamically to the UI."""
    if indicator in additional_indicators:
        return  # Prevent duplicates

    frame = tk.Frame(dynamic_frame, bg="#1C1C2E")
    frame.pack()

    # Create a checkbox for the indicator
    indicator_var = tk.IntVar(value=is_selected)
    indicator_checkbox = tk.Checkbutton(
        frame,
        text=indicator,
        variable=indicator_var,
        bg="#1C1C2E",
        fg="white",
        selectcolor="#1C1C2E"
    )
    indicator_checkbox.pack(side="left")

    # Create an entry field for the value
    value_label = tk.Label(frame, text="Value:", fg="white", bg="#1C1C2E")
    value_label.pack(side="left")
    value_entry = tk.Entry(frame)
    value_entry.pack(side="left")
    value_entry.insert(0, value)

    # Save the indicator's state
    additional_indicators[indicator] = {"var": indicator_var, "entry": value_entry}

    # Update the dropdown to exclude the selected indicator
    indicators.remove(indicator)
    update_dropdown_menu(dropdown, indicators, additional_indicators, selected_indicator)

    # Handle deselection (removal) of the indicator
    def toggle_indicator():
        if indicator_var.get() == 0:  # Checkbox deselected
            # Remove UI components
            frame.destroy()

            # Add the indicator back to the dropdown menu
            indicators.append(indicator)
            del additional_indicators[indicator]  # Remove from active indicators

            # Update dropdown menu immediately
            update_dropdown_menu(dropdown, indicators, additional_indicators, selected_indicator)

    # Bind deselection to checkbox
    indicator_checkbox.config(command=toggle_indicator)


def load_strategy(rsi_var, macd_var, rsi_entry, macd_entry, dynamic_frame, additional_indicators, dropdown, indicators, selected_indicator):
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
                add_indicator_to_ui(
                    dynamic_frame,
                    key,
                    data.get("selected", 0),
                    data.get("value", ""),
                    additional_indicators,
                    dropdown,
                    indicators,
                    selected_indicator
                )

            # Ensure dropdown reflects only unticked indicators
            update_dropdown_menu(dropdown, indicators, additional_indicators, selected_indicator)

            print("Strategy loaded successfully!")
        else:
            print("No strategies found in the database.")
    except Exception as e:
        print(f"Error loading strategy: {e}")


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

    # Add indicator button
    add_indicator_button = tk.Button(
        strategy_content,
        text="Add Indicator",
        command=lambda: add_indicator_to_ui(
            dynamic_frame,
            selected_indicator.get(),
            1,
            "",
            additional_indicators,
            dropdown,
            indicators,
            selected_indicator,
        ),
        bg="#1C1C2E",
        fg="white",
    )
    add_indicator_button.pack(pady=10)

    def save_strategy():
        """Save the strategy."""
        # Capture values from UI components
        rsi_selected = rsi_var.get()
        macd_selected = macd_var.get()
        rsi_threshold = rsi_entry.get() or None  # Default to None if empty
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
        print(f"Additional Indicators: {additional_data}")  # Debug statement

        # Convert thresholds to floats if they exist
        try:
            rsi_threshold = float(rsi_threshold) if rsi_threshold else None
            macd_threshold = float(macd_threshold) if macd_threshold else None
        except ValueError:
            print("Error: Invalid threshold value.")
            return

        # Save the strategy in the database
        try:
            conn = create_connection()
            cursor = conn.cursor()

            # Check if a strategy already exists
            cursor.execute("SELECT COUNT(*) FROM strategies;")
            strategy_exists = cursor.fetchone()[0] > 0

            if strategy_exists:
                # Update the existing strategy
                cursor.execute("""
                    UPDATE strategies
                    SET rsi_selected = ?, macd_selected = ?, rsi_threshold = ?, macd_threshold = ?, additional_indicators = ?
                """, (rsi_selected, macd_selected, rsi_threshold, macd_threshold, json.dumps(additional_data)))
                print("Strategy updated successfully!")
            else:
                # Insert a new strategy if none exists
                cursor.execute("""
                    INSERT INTO strategies (rsi_selected, macd_selected, rsi_threshold, macd_threshold, additional_indicators)
                    VALUES (?, ?, ?, ?, ?)
                """, (rsi_selected, macd_selected, rsi_threshold, macd_threshold, json.dumps(additional_data)))
                print("Strategy saved successfully!")

            conn.commit()
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

    # Load the saved strategy on page load
    load_strategy(
        rsi_var,
        macd_var,
        rsi_entry,
        macd_entry,
        dynamic_frame,
        additional_indicators,
        dropdown,
        indicators,
        selected_indicator,
    )
