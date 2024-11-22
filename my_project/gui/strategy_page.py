import tkinter as tk
from tkinter import ttk
from gui.shared_components import show_frame, center_frame
import json
from data.db_handler import create_connection


def update_dropdown_menu(dropdown, indicators, additional_indicators, selected_indicator):
    """Update the dropdown menu to show only unticked indicators."""
    dropdown['menu'].delete(0, "end")
    unticked = [i for i in indicators if i not in additional_indicators]
    for ind in unticked:
        dropdown['menu'].add_command(label=ind, command=lambda val=ind: selected_indicator.set(val))


def add_indicator_ui(indicator, frame, indicators, additional_indicators, dropdown, selected_indicator):
    """Add or update an indicator dynamically in the UI."""
    if indicator in additional_indicators:
        return  # Prevent duplicates

    ui_frame = tk.Frame(frame, bg="#1C1C2E")
    ui_frame.pack()

    var = tk.IntVar(value=1)
    checkbox = tk.Checkbutton(
        ui_frame,
        text=indicator,
        variable=var,
        bg="#1C1C2E",
        fg="white",
        selectcolor="#1C1C2E",
        command=lambda: toggle_indicator(var, ui_frame, indicator, indicators, additional_indicators, dropdown, selected_indicator)
    )
    checkbox.pack(side="left", padx=5)

    entry = tk.Entry(ui_frame, validate="key", validatecommand=(frame.register(validate_integer_input), "%P"))
    entry.pack(side="left", padx=5)

    # Store state in additional indicators
    additional_indicators[indicator] = {"var": var, "entry": entry}
    update_dropdown_menu(dropdown, indicators, additional_indicators, selected_indicator)


def toggle_indicator(var, ui_frame, indicator, indicators, additional_indicators, dropdown, selected_indicator):
    """Handle indicator removal from UI and update dropdown menu."""
    if not var.get():  # Deselect
        ui_frame.destroy()
        if indicator not in indicators:
            indicators.append(indicator)  # Add back to available indicators
            indicators.sort()  # Keep dropdown sorted
        del additional_indicators[indicator]
        update_dropdown_menu(dropdown, indicators, additional_indicators, selected_indicator)


def validate_integer_input(value):
    """Ensure only integers or empty values are allowed."""
    return value == "" or value.isdigit()


def save_strategy_to_db(rsi, macd, rsi_thresh, macd_thresh, additional_data):
    """Save the strategy to the database."""
    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Save or update the strategy
        cursor.execute("DELETE FROM strategies")
        cursor.execute(
            """
            INSERT INTO strategies (rsi_selected, macd_selected, rsi_threshold, macd_threshold, additional_indicators)
            VALUES (?, ?, ?, ?, ?)
            """,
            (rsi, macd, rsi_thresh, macd_thresh, json.dumps(additional_data)),
        )
        conn.commit()
        print("Strategy saved successfully!")
    except Exception as e:
        print(f"Error saving strategy: {e}")
    finally:
        conn.close()


def load_strategy(rsi_var, macd_var, rsi_entry, macd_entry, dynamic_frame, additional_indicators, indicators, dropdown, selected_indicator):
    """Load the last saved strategy and populate the UI."""
    try:
        conn = create_connection()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM strategies ORDER BY rowid DESC LIMIT 1").fetchone()
        conn.close()

        if row:
            # Update RSI and MACD selection and thresholds
            rsi_var.set(row[0])
            macd_var.set(row[1])

            rsi_entry.delete(0, tk.END)
            if row[2] is not None:
                rsi_entry.insert(0, str(int(row[2])))

            macd_entry.delete(0, tk.END)
            if row[3] is not None:
                macd_entry.insert(0, str(int(row[3])))

            # Parse and load additional indicators
            additional_data = json.loads(row[4]) if row[4] else {}
            for key, data in additional_data.items():
                if key not in additional_indicators:
                    # Add UI elements for the additional indicator
                    add_indicator_ui(
                        key,
                        dynamic_frame,
                        indicators,
                        additional_indicators,
                        dropdown,
                        selected_indicator,
                    )
                    # Set the checkbox and entry field values
                    indicator_data = additional_indicators[key]
                    indicator_data["var"].set(data["selected"])
                    indicator_data["entry"].delete(0, tk.END)
                    indicator_data["entry"].insert(0, data["value"])

            # Update dropdown menu to reflect unticked indicators
            update_dropdown_menu(dropdown, indicators, additional_indicators, selected_indicator)

            print("Strategy loaded successfully!")
        else:
            print("No strategies found in the database.")
    except Exception as e:
        print(f"Error loading strategy: {e}")


def create_strategy_page(root, strategy_frame, main_frame):
    """Set up the enhanced strategy builder page."""
    strategy_frame.configure(bg="#1C1C2E")
    center_frame(strategy_frame)

    strategy_content = tk.Frame(strategy_frame, bg="#1C1C2E")
    strategy_content.grid(row=0, column=0)

    tk.Label(strategy_content, text="Strategy Builder", font=('Helvetica', 16), fg="white", bg="#1C1C2E").pack(pady=20)

    rsi_var = tk.IntVar()
    macd_var = tk.IntVar()
    additional_indicators = {}
    indicators = ["Bollinger Bands", "Moving Average", "Stochastic Oscillator"]
    selected_indicator = tk.StringVar(value="Select an Indicator")

    tk.Checkbutton(
        strategy_content, text="RSI", variable=rsi_var, bg="#1C1C2E", fg="white", selectcolor="#1C1C2E"
    ).pack()
    rsi_entry = tk.Entry(strategy_content, validate="key", validatecommand=(root.register(validate_integer_input), "%P"))
    rsi_entry.pack(pady=5)
    tk.Label(strategy_content, text="RSI Threshold:", fg="white", bg="#1C1C2E").pack()

    tk.Checkbutton(
        strategy_content, text="MACD", variable=macd_var, bg="#1C1C2E", fg="white", selectcolor="#1C1C2E"
    ).pack()
    macd_entry = tk.Entry(strategy_content, validate="key", validatecommand=(root.register(validate_integer_input), "%P"))
    macd_entry.pack(pady=5)
    tk.Label(strategy_content, text="MACD Threshold:", fg="white", bg="#1C1C2E").pack()

    indicator_frame = tk.Frame(strategy_content, bg="#1C1C2E")  # New frame for dropdown and button
    indicator_frame.pack(pady=10)

    dropdown = ttk.OptionMenu(indicator_frame, selected_indicator, *indicators)
    dropdown.pack(side="left", padx=5)  # Dropdown aligned to the left in the new frame

    dynamic_frame = tk.Frame(strategy_content, bg="#1C1C2E")
    dynamic_frame.pack()

    add_button = tk.Button(
        indicator_frame,
        text="Add Indicator",
        bg="#1C1C2E",
        fg="white",
        command=lambda: add_indicator_ui(
            selected_indicator.get(),
            dynamic_frame,
            indicators,
            additional_indicators,
            dropdown,
            selected_indicator,
        ),
    )
    add_button.pack(side="left", padx=5)  # Button placed to the right of the dropdown

    def save_strategy():
        """Validate and save the strategy."""
        validation_failed = False

        # Validate RSI
        if rsi_var.get() and not rsi_entry.get():
            rsi_entry.config(bg="red")
            validation_failed = True
        else:
            rsi_entry.config(bg="white")

        # Validate MACD
        if macd_var.get() and not macd_entry.get():
            macd_entry.config(bg="red")
            validation_failed = True
        else:
            macd_entry.config(bg="white")

        # Validate additional indicators
        for key, data in additional_indicators.items():
            if data["var"].get() and not data["entry"].get():
                data["entry"].config(bg="red")
                validation_failed = True
            else:
                data["entry"].config(bg="white")

        if validation_failed:
            print("Validation failed. Fix highlighted fields.")
            return

        # Save to DB
        save_strategy_to_db(
            rsi_var.get(),
            macd_var.get(),
            rsi_entry.get() or None,
            macd_entry.get() or None,
            {
                key: {"selected": data["var"].get(), "value": data["entry"].get()}
                for key, data in additional_indicators.items()
            },
        )
        print("Strategy saved successfully!")

    tk.Button(
        strategy_content,
        text="Save Strategy",
        bg="#1C1C2E",
        fg="white",
        command=save_strategy,
    ).pack(pady=10)

    tk.Button(strategy_content, text="Back", bg="#1C1C2E", fg="white", command=lambda: show_frame(main_frame)).pack(pady=10)

    load_strategy(
        rsi_var,
        macd_var,
        rsi_entry,
        macd_entry,
        dynamic_frame,
        additional_indicators,
        indicators,
        dropdown,
        selected_indicator,
    )
