from tkinter import *
from tkinter import ttk
import widgets


def main():
    # Create the main window and initialise the TK interpreter.
    root = Tk()
    configure_window(root)

    # Create a frame for sub-widgets.
    create_button_arry(root)

    # Launch the UI
    root.mainloop()


def configure_window(root):
    # Window title
    root.title("4000 Weeks")

    # Launch Size
    window_width = 1024
    window_height = 576

    # Get the screen dimension
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Find the center point
    center_x = int(screen_width/2 - window_width / 2)
    center_y = int(screen_height/2 - window_height / 2)

    # Set the position of the window to the center of the screen
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    # Set the minimum window size
    root.minsize(window_width, window_height)

    # Remove the icon
    root.iconbitmap("")

def create_button_arry(root, rows=5, columns=5):
    button_frame = ttk.Frame(root, padding=10)
    button_frame.grid()

    for i in range(rows):
        for j in range(columns):
            widgets.week_button(button_frame, command=root.destroy).grid(column=j, row=i)

if __name__ == "__main__":
    main()