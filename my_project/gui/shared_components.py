# gui/shared_components.py
def show_frame(frame):
    """Raise the specified frame to the top."""
    frame.tkraise()

def toggle_fullscreen(root):
    """Toggle fullscreen mode for the Tkinter window."""
    root.attributes("-fullscreen", not root.attributes("-fullscreen"))

def center_frame(frame):
    """
    Configures a frame to center its content by setting row and column weights.
    """
    frame.rowconfigure(0, weight=1)  # Center vertically
    frame.columnconfigure(0, weight=1)  # Center horizontally
