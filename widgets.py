from tkinter import *
from tkinter import ttk

# ---------------- #
# BUTTON WIDGET
# ---------------- #
class week_button(ttk.Button):
    def __init__(self, parent, **kwargs):
        defaults = {
            ['fg']: "#262626",
            ['bg']: "#f4f4f4",
            ['font']: ('arial', 14, 'normal'),
            ['relief']: 'raised',
            ['borderwidth']: 0,
            ['cursor']: 'hand2',  # Hand cursor on hover
            ['padx']: 20,
            ['width']: 10,
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)