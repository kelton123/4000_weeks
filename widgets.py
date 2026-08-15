import tkinter as tk
import styles

class ButtonText(tk.Button):
    def __init__(self, parent, **kwargs):
        defaults = {
            "font"   : styles.BODY,
            "bg"     : styles.FUTURE_COLOR,
            "fg"     : styles.TEXT_FG,
            "relief" : 'flat',
            "cursor" :'hand2',
            "padx"   : 14
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

class ButtonTextActive(tk.Button):
    def __init__(self, parent, **kwargs):
        defaults = {
            "font"   : styles.BODY_BOLD,
            "bg"     : styles.NOW_COLOR,
            "fg"     : styles.BG,
            "relief" : 'flat',
            "cursor" :'hand2',
            "padx"   : 14
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)


# ── Week Cell Widget ────────────────────────────────────────────────────────────

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