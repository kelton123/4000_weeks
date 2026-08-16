import tkinter as tk
import styles


# ── FRAME WIDGETS ────────────────────────────────────────────────────────────

# Default frame with minimal customisation.
class Frame(tk.Frame):
    def __init__(self, parent, **kwargs):
        defaults = {
            "bg" : styles.BG
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

# Default frame with minimal customisation.
class FrameSpacerH100(tk.Frame):
    def __init__(self, parent, **kwargs):
        defaults = {
            "bg"     : styles.BG,
            "height" : 100
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

# ── BUTTON WIDGETS ────────────────────────────────────────────────────────────

# Text button default.
class ButtonText(tk.Button):
    def __init__(self, parent, **kwargs):
        defaults = {
            "font"   : styles.BODY,
            "bg"     : styles.SURFACE,
            "fg"     : styles.TEXT_FG,
            "relief" : 'flat',
            "cursor" :'hand2',
            "padx"   : 14
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

# Text button active.
class ButtonTextActive(tk.Button):
    def __init__(self, parent, **kwargs):
        defaults = {
            "font"   : styles.BODY_BOLD,
            "bg"     : styles.ACCENT,
            "fg"     : styles.ACCENT_FG,
            "relief" : 'flat',
            "cursor" :'hand2',
            "padx"   : 14
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

        # Marks this widget as always using the fixed ACCENT/ACCENT_FG
        # pairing rather than the live theme colours, so App._toggle_theme
        # knows to skip repainting it - see the note there for why that
        # matters (ACCENT_FG intentionally shares a literal value with
        # BG_DARK, which would otherwise get swept up by the theme walk).
        self.theme_locked = True

# Icon button default
class ButtonImage(tk.Label):
    def __init__(self, parent, **kwargs):
        defaults = {
            "bg"     : styles.BG,
            "cursor" : "hand2",
            "padx"   : 5,
            "pady"   : 5
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

        # Bind the mouse entering and leaving to update the background colour.
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        ''' Update the background colour to indicate hovering. '''
        self.config(bg = styles.SURFACE)
        
    def on_leave(self, event):
        ''' Update the background colour to the default. '''
        self.config(bg = styles.BG)


# ── LABEL WIDGETS ────────────────────────────────────────────────────────────

# Header 01
class H1Label(tk.Label):
    def __init__(self, parent, **kwargs):
        defaults = {
            "font" : styles.H1,
            "fg"   : styles.TEXT_FG,
            "bg"   : styles.BG,
            
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

# Header 02
class H2Label(tk.Label):
    def __init__(self, parent, **kwargs):
        defaults = {
            "font" : styles.H2,
            "fg"   : styles.TEXT_FG,
            "bg"   : styles.BG,
            
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

# Header 03
class H3Label(tk.Label):
    def __init__(self, parent, **kwargs):
        defaults = {
            "font" : styles.H3,
            "fg"   : styles.TEXT_FG,
            "bg"   : styles.BG,
            
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


# Body Text
class BodyLabel(tk.Label):
    def __init__(self, parent, **kwargs):
        defaults = {
            "font" : styles.BODY,
            "fg"   : styles.TEXT_FG,
            "bg"   : styles.BG,
            
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

class BodyBoldLabel(tk.Label):
    def __init__(self, parent, **kwargs):
        defaults = {
            "font" : styles.BODY_BOLD,
            "fg"   : styles.TEXT_FG,
            "bg"   : styles.BG,
            
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


# Caption Text
class CaptionLabel(tk.Label):
    def __init__(self, parent, **kwargs):
        defaults = {
            "font" : styles.LABEL,
            "fg"   : styles.TEXT_FG,
            "bg"   : styles.BG,
            
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


# ── ENTRY WIDGET ────────────────────────────────────────────────────────────────

# Single line entry default
class EntrySingleLineBody(tk.Entry):
    def __init__(self, parent, **kwargs):
        defaults = {
            "font"   : styles.BODY,
            "fg"     : styles.TEXT_FG,
            "bg"     : styles.SURFACE,
            "relief" : "flat"
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

# Multi-line entry default
class EntryMultilineBody(tk.Text):
    def __init__(self, parent, **kwargs):
        defaults = {
            "height"           : 5,
            "bg"               : styles.SURFACE,
            "fg"               : styles.TEXT_FG,
            "insertbackground" : styles.TEXT_FG,
            "relief"           : "flat",
            "font"             : styles.BODY,
            "wrap"             : "word"
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


# ── WEEK CELL WIDGET ────────────────────────────────────────────────────────────

class Week_Cell:
    def __init__(
            self,
            id          :int,
            year        :int,
            week        :int,
            label       :str,
            colour      :str,
            rectangle,
            image_paths = None,
            description = "",
            category    = "Select Category"):
        
        self.id = id
        self.year        = year
        self.week        = week
        self.label       = label
        self.colour      = colour
        self.cell        = rectangle
        
        # Optional metadata which is added by the user.
        self.image_paths = image_paths if image_paths is not None else []
        self.description = description
        self.category    = category
        
        # Getter for week_number
        @property
        def id(self):
            return self._week_number
        
        @id.setter
        def id(self, number :int):
            self._week_number = number

        @property
        def year(self):
            return self._year
        
        @year.setter
        def year(self, year_value :int):
            self._year = year_value

        @property
        def week(self):
            return self._week
        
        @week.setter
        def week(self, week_value :int):
            self._week = week_value

        @property
        def label(self):
            return self._label
        
        @label.setter
        def label(self, label_type :str):
            self._label = label_type
        
        @property
        def colour(self):
            return self._colour
        
        @colour.setter
        def colour(self, colour_value :str):
            self._colour = colour_value

        @property
        def rectangle(self):
            return self._rectangle
        
        @rectangle.setter
        def rectangle(self, canvas_rect):
            self._rectangle = canvas_rect