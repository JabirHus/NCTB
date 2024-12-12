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

    # Create a frame for the indicator
    ui_frame = tk.Frame(frame, bg="#1C1C2E")
    ui_frame.pack(pady=5, fill="x", anchor="w")  # Align to the left

    # Create a variable to manage the checkbox state
    var = tk.IntVar(value=1)

    # Add the checkbox for the indicator
    checkbox = tk.Checkbutton(
        ui_frame,
        text=indicator,
        variable=var,
        bg="#1C1C2E",
        fg="white",
        selectcolor="#1C1C2E",
        width=20,  # Fixed width for consistent alignment
        anchor="w",
        command=lambda: toggle_indicator(
            var, ui_frame, indicator, indicators, additional_indicators, dropdown, selected_indicator
        )
    )
    checkbox.grid(row=0, column=0, padx=(10, 20), sticky="w")  # Checkbox in the first column

    # Add a sub-frame for sub-indicators
    sub_frame = tk.Frame(ui_frame, bg="#1C1C2E")
    sub_frame.grid(row=0, column=1, sticky="w")  # Sub-indicators in the second column

    # Indicator-specific settings
    indicator_settings = {
        "RSI": {"Period": ("14", None, None), "Undersold": ("30", lambda x: x < 50, "must be < 50"), "Oversold": ("70", lambda x: x > 50, "must be > 50")},
        "MACD": {"Fast EMA": ("12", None, None), "Slow EMA": ("26", None, None), "MACD SMA": ("9", None, None)},
        "Bollinger Bands": {"Period": ("20", lambda x: x > 0, "must be > 0"), "Deviation": ("2", lambda x: x > 0, "must be > 0"), "Shift": ("0", None, None)},
        "Stochastic Oscillator": {"%K Period": ("5", lambda x: x > 0, "must be > 0"), "%D Period": ("3", lambda x: x > 0, "must be > 0"), "Slowing": ("3", lambda x: x > 0, "must be > 0")},
        "Moving Average": {"Period": ("10", lambda x: x > 0, "must be > 0"), "Shift": ("0", None, None)}
    }

    # Add sub-indicators for the selected indicator
    if indicator in indicator_settings:
        sub_indicators = indicator_settings[indicator]
        vars_dict = {}
        col_index = 0
        for sub_ind, (placeholder, validation, message) in sub_indicators.items():
            add_sub_indicator_ui(sub_frame, vars_dict, sub_ind, placeholder, validation, message, col_index)
            col_index += 2  # Increment column for each sub-indicator
        additional_indicators[indicator] = {"var": var, "sub_indicators": vars_dict, "frame": ui_frame}
    else:
        # If no sub-indicators, add a single entry
        entry = tk.Entry(sub_frame, width=15)
        entry.grid(row=0, column=1, padx=5, sticky="w")
        additional_indicators[indicator] = {"var": var, "entry": entry, "frame": ui_frame}

    update_dropdown_menu(dropdown, indicators, additional_indicators, selected_indicator)


def add_sub_indicator_ui(sub_frame, vars_dict, sub_ind, placeholder, validation, message, col_index):
    """Add sub-indicator UI components, aligned horizontally in one line."""
    label = tk.Label(
        sub_frame,
        text=sub_ind,
        width=10,
        bg="#1C1C2E",
        fg="white"
    )
    label.grid(row=0, column=col_index, padx=(10, 5), pady=2, sticky="w")  # Left-align label in the specified column

    entry = tk.Entry(sub_frame, width=10, fg="grey", font=("Helvetica", 10))
    entry.insert(0, placeholder)

    def clear_placeholder(event, e=entry, p=placeholder):
        if e.get() == p:
            e.delete(0, tk.END)
            e.config(fg="black", font=("Helvetica", 10, "bold"))

    def restore_placeholder(event, e=entry, p=placeholder):
        if not e.get():
            e.insert(0, p)
            e.config(fg="grey", font=("Helvetica", 10))

    entry.bind("<FocusIn>", clear_placeholder)
    entry.bind("<FocusOut>", restore_placeholder)
    entry.grid(row=0, column=col_index + 1, padx=(0, 10), pady=2, sticky="w")  # Align entry to the right of the label

    vars_dict[sub_ind] = {"entry": entry, "validation": validation, "message": message}

def toggle_indicator(var, ui_frame, indicator, indicators, additional_indicators, dropdown, selected_indicator):
    """Handle indicator removal from UI and update dropdown menu."""
    if not var.get():  # Deselect
        ui_frame.destroy()
        if indicator not in indicators:
            indicators.append(indicator)  # Add back to available indicators
            indicators.sort()  # Keep dropdown sorted
        if indicator in additional_indicators:
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
                    if "sub_indicators" in data:
                        for sub_key, sub_data in data["sub_indicators"].items():
                            indicator_data = additional_indicators[key]["sub_indicators"][sub_key]
                            indicator_data["entry"].delete(0, tk.END)
                            indicator_data["entry"].insert(0, sub_data["value"])
                            indicator_data["entry"].config(fg="black", font=("Helvetica", 10, "bold"))
                    else:
                        indicator_data = additional_indicators[key]
                        indicator_data["var"].set(data["var"])
                        indicator_data["entry"].delete(0, tk.END)
                        indicator_data["entry"].insert(0, data["value"])
                        indicator_data["entry"].config(fg="black", font=("Helvetica", 10, "bold"))

            update_dropdown_menu(dropdown, indicators, additional_indicators, selected_indicator)

            print("Strategy loaded successfully!")
        else:
            print("No strategies found in the database.")
    except Exception as e:
        print(f"Error loading strategy: {e}")

def validate_inputs(additional_indicators, error_label):
    """Validate that all selected indicators have valid inputs."""
    errors = []

    # Base case: Check if no indicators are selected
    if not additional_indicators:
        error_label.config(text="You must select an indicator(s) to build your strategy.", fg="red")
        return ["No indicators selected."]
    
    for key, data in additional_indicators.items():
        if "sub_indicators" in data:
            for sub_key, sub_data in data["sub_indicators"].items():
                value = sub_data["entry"].get()
                try:
                    int_value = int(value)  # Ensure it's an integer
                    if sub_data["validation"] and not sub_data["validation"](int_value):
                        errors.append(f"{key} ({sub_key}): {sub_data['message']}")
                        sub_data["entry"].configure(bg="red")
                    else:
                        sub_data["entry"].configure(bg="white")
                except ValueError:
                    errors.append(f"{key} ({sub_key}): Value must be an integer.")
                    sub_data["entry"].configure(bg="red")
        else:
            if data["var"].get():
                value = data["entry"].get()
                try:
                    int_value = int(value)  # Ensure it's an integer
                    data["entry"].configure(bg="white")
                except ValueError:
                    errors.append(f"{key}: Value must be an integer.")
                    data["entry"].configure(bg="red")

    error_label.config(text="\n".join(errors) if errors else "", fg="red" if errors else "green")
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

    tk.Label(strategy_content, text="", bg="#1C1C2E").pack()

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

    error_label = tk.Label(strategy_content, text="", font=("Helvetica", 10), fg="red", bg="#1C1C2E")
    error_label.pack(pady=10)

    def save_strategy():
        """Validate inputs and save the strategy."""
        errors = validate_inputs(additional_indicators, error_label)

        if errors:
            print("Validation Errors:", errors)
            return

        try:
            save_strategy_to_db({
                key: {
                    "sub_indicators": {
                        sub_key: {"value": sub_data["entry"].get()}
                        for sub_key, sub_data in data["sub_indicators"].items()
                    },
                    "var": data["var"].get()
                } if "sub_indicators" in data else {
                    "var": data["var"].get(), "value": data["entry"].get()
                }
                for key, data in additional_indicators.items()
            })
            error_label.config(text="Strategy saved successfully!", fg="green")
        except Exception as e:
            error_label.config(text=f"Error saving strategy: {e}", fg="red")

    tk.Label(strategy_content, text="", bg="#1C1C2E").pack()

    tk.Button(
        strategy_content,
        text="Save Strategy",
        bg="#1C1C2E",
        fg="white",
        command=save_strategy,
    ).pack(pady=10)

    tk.Button(strategy_content, text="Back", bg="#1C1C2E", fg="white", command=lambda: show_frame(main_frame)).pack(pady=10)

    load_strategy(dynamic_frame, additional_indicators, indicators, dropdown, selected_indicator)
