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

    entry = tk.Entry(ui_frame)
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


def save_strategy_to_db(additional_data):
    """Save the strategy to the database."""
    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Save or update the strategy
        cursor.execute("DELETE FROM strategies")
        cursor.execute(
            """
            INSERT INTO strategies (additional_indicators)
            VALUES (?)
            """,
            (json.dumps(additional_data),),
        )
        conn.commit()
        print("Strategy saved successfully!")
    except Exception as e:
        print(f"Error saving strategy: {e}")
    finally:
        conn.close()


def load_strategy(dynamic_frame, additional_indicators, indicators, dropdown, selected_indicator):
    """Load the last saved strategy and populate the UI."""
    try:
        conn = create_connection()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM strategies LIMIT 1").fetchone()
        conn.close()

        if row:
            # Parse and load additional indicators
            additional_data = json.loads(row[0]) if row[0] else {}
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


def validate_inputs(additional_indicators):
    """Validate that all selected indicators have valid inputs."""
    errors = []
    for key, data in additional_indicators.items():
        if data["var"].get():  # If indicator is selected
            value = data["entry"].get()
            if not value.isdigit():  # Check if the value is a valid integer
                errors.append(f"{key}: Value must be an integer.")

    return errors


def create_strategy_page(root, strategy_frame, main_frame):
    """Set up the enhanced strategy builder page."""
    strategy_frame.configure(bg="#1C1C2E")
    center_frame(strategy_frame)

    strategy_content = tk.Frame(strategy_frame, bg="#1C1C2E")
    strategy_content.grid(row=0, column=0)

    tk.Label(strategy_content, text="Strategy Builder", font=('Helvetica', 16), fg="white", bg="#1C1C2E").pack(pady=20)

    additional_indicators = {}
    indicators = ["RSI", "MACD", "Bollinger Bands", "Moving Average", "Stochastic Oscillator"]
    selected_indicator = tk.StringVar(value="Select an Indicator")

    dropdown_frame = tk.Frame(strategy_content, bg="#1C1C2E")
    dropdown_frame.pack()

    dropdown = ttk.OptionMenu(dropdown_frame, selected_indicator, *indicators)
    dropdown.pack(side="left", pady=10, padx=5)

    tk.Button(
        dropdown_frame,
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
    ).pack(side="left", padx=5)

    dynamic_frame = tk.Frame(strategy_content, bg="#1C1C2E")
    dynamic_frame.pack()

    def save_strategy():
        """Validate inputs and save the strategy."""
        errors = validate_inputs(additional_indicators)

        if errors:
            # Highlight invalid fields in red
            for key, data in additional_indicators.items():
                if data["var"].get():
                    value = data["entry"].get()
                    if not value.isdigit():
                        data["entry"].configure(bg="red")  # Highlight invalid input
                    else:
                        data["entry"].configure(bg="white")  # Reset valid inputs
            print("Validation Errors:", errors)
            return  # Stop saving if there are validation errors

        # Reset input field highlights
        for key, data in additional_indicators.items():
            data["entry"].configure(bg="white")

        try:
            # Save to the database
            save_strategy_to_db({
                key: {"selected": indicator["var"].get(), "value": indicator["entry"].get()}
                for key, indicator in additional_indicators.items()
            })
        except Exception as e:
            print(f"Error saving strategy: {e}")


    tk.Button(
        strategy_content,
        text="Save Strategy",
        bg="#1C1C2E",
        fg="white",
        command=save_strategy,
    ).pack(pady=10)

    tk.Button(strategy_content, text="Back", bg="#1C1C2E", fg="white", command=lambda: show_frame(main_frame)).pack(pady=10)

    load_strategy(dynamic_frame, additional_indicators, indicators, dropdown, selected_indicator)
