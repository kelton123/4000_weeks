import json
import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import date, datetime, timedelta

from PIL import Image, ImageTk, ImageOps

# Custom Widgets
import widgets

# Style Constants
import styles

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for py2app bundle."""
    # os.path.abspath(__file__) points inside Contents/Resources/ when running in py2app
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("4000 Weeks")
        self.root.configure(bg=styles.BG)
        self._center((styles.CANVAS_WIDTH + 20), 540)
        self.root.state("zoomed")

        # ── Runtime state ─────────────────────────────────────────
        self._custom_labels : list[dict]                          = []   # [{name, color}, …]
        self._week_labels   : dict[int, int]                      = {}   # week_num → label index
        self._week_notes    : dict[int, dict]                     = {}   # week_num → {description, image_paths, category}
        self._photo_cache   : dict[int, list[ImageTk.PhotoImage]] = {}   # keeps refs alive (list per week, up to 4 thumbnails)
        self.week_cells     : list[widgets.Week_Cell]             = []

        self._weeks_lived   = 0
        self._total_weeks   = 0
        self._dob           = None
        self._click_pending = None   # after() ID for delayed single-click
        self._tooltip_win:  tk.Toplevel | None = None
        self._tooltip_week: int | None = None
        self._tooltip_buttons: tk.Toplevel | None = None

        self._dark_mode = True

        # Handle unsaved changes to append '*' for unsaved work
        self._dirty = False
        self._birthday_text = "Add Birthday"
        self.active_file_path = None

        self._build_ui()
        self._refresh()
        self.root.after(50, self._fix_scrollregion)

        # ── KEYBOARD BINDINGS ───────────────────────────────────────────────────────────
        # Save the file
        self.root.bind("<Command-s>", self.save_data)
        self.root.bind("<Control-s>", self.save_data)

        # Open a file
        self.root.bind("<Command-o>", self.load_data)
        self.root.bind("<Control-o>", self.load_data)

        # Toggle theme colours
        self.root.bind("<Command-t>", self._toggle_theme)
        self.root.bind("<Control-t>", self._toggle_theme)

    # ── Window setup ──────────────────────────────────────────────────────────

    def _take_focus(self, event: tk.Event = None):
        '''
        Used to take the focus from sub-widgets like entry or comboxes and make the clicked widget's toplevel
        window to take the focus.
        '''
        if  event or event.widget:
            widget = event.widget

            if isinstance(widget, (tk.Entry, tk.Text, ttk.Entry, ttk.Combobox, tk.Spinbox)):
                widget.focus_set()
                return

            # Focus background widgets like frames, canvases, labels and toplevel windows.
            widget.winfo_toplevel().focus_set()

    def _center(self, width: int, height: int):
        '''
        Used to center the window in the screen on startup.
        The default is the top left corner of the screen.

        @param width  : The minimum window width. Should be in the ratio of 16x9.
        @param height : The minimum window height. Should be in the ration os 16x9.
        @return       : N/A
        @raise        : N/A
        '''

        # Calculate the center of the active screen and set the geometry.
        screen_width, screen_height = self.get_screen_dims()
        self.root.geometry(f'{width}x{height}+{(screen_width - width) // 2}+{(screen_height - height) // 2}')

        # Set the minimum screen size for the window.
        self.root.minsize(width, height)

    def get_screen_dims(self) -> tuple:
        '''
        Gets the width and the height of the active screen in pixels.

        @param                : N/A
        @return screen_width  : The number of pixels in the X direction.
        @return screen_height : The number of pixels in the Y direction.
        @raise                : N/A 
        '''
        return self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    # ── Page-level scroll container ───────────────────────────────────────────

    def _build_ui(self):
        '''
        Builds each section of the UI.
        The structure is similar to a website with a page which holds sections.

        @param  : N/A
        @return : N/A
        @raise  : N/A
        '''

        # Create scrollbar for the window.
        scrollbar = ttk.Scrollbar(self.root, orient='vertical')
        scrollbar.pack(side='right', fill='y')

        # Create the parent page to contain all of the subsections.
        self._page = tk.Canvas(
            self.root,
            bg                   = styles.BG,
            highlightthickness   = 0,
            yscrollcommand       = scrollbar.set
            )
        self._page.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self._page.yview)

        self._content = widgets.Frame(self._page)
        self._win_id  = self._page.create_window(
            0,
            0,
            anchor='nw',
            window=self._content
            )

        # Bind inputs from the user for the page, content frame and window.
        self._page.bind('<Configure>',     self._on_page_resize)
        self._content.bind('<Configure>',  self._on_content_resize)
        self.root.bind_all('<MouseWheel>', self._scroll)

        # Build all of the sub-sections
        self._build_header()
        self._build_controls()
        self._build_grid()
        self._build_footer()

    def _on_page_resize(self, event: tk.Event):
        self._page.itemconfig(self._win_id, width=event.width)

    def _on_content_resize(self, _: tk.Event):
        self._page.config(scrollregion=self._page.bbox('all'))

    def _fix_scrollregion(self):
        self._content.update_idletasks()
        self._page.config(scrollregion=self._page.bbox('all'))

    def _scroll(self, event: tk.Event):
        self._page.yview_scroll(-1 * (event.delta // 120), 'units')

    # ── UI sections ───────────────────────────────────────────────────────────

    def _build_header(self):
        '''
        The header section with the year that the grid is working with. This label can be clicked to
        launch a popup which enables a different date to be entered. However, this will delete all metadata
        in the project unless saved.

        @param  : N/A
        @return : N/A
        @raise  : N/A
        '''

        # Create a frame to keep the header section the same width as the grid section.
        frame = widgets.Frame(self._content, width=styles.CANVAS_WIDTH, height=80)
        frame.pack(pady=(100, 2))
        frame.pack_propagate(False)

        # The active birthday - default text is "Add birthday".
        self.birthday = widgets.H1Label(frame, text="Add Birthday", cursor="hand2")
        self.birthday.pack(ipadx=50)

        # Bind clicking the birthday label to allow a new date to be visualised.
        self.birthday.bind("<Button-1>", lambda event: self.open_birthday_popup())
        self.birthday.bind("<Enter>", self.highlight_background, add="+")
        self.birthday.bind("<Leave>", self.reset_background, add="+")

        self.birthday.bind("<Enter>", lambda event: self._show_tooltip_buttons(tooltip_text="Update date", event=event), add="+")
        self.birthday.bind("<Motion>", self._update_tooltip_position, add='+')
        self.birthday.bind("<Leave>", self._hide_tooltip_buttons, add="+")

    def _load_icon(self, path: str, size: tuple = (20, 20)) -> ImageTk.PhotoImage:
        '''
        Loads and resizes an icon image for use on a toolbar button.

        @param path : Path to the icon image file.
        @param size : (width, height) in pixels to resize the icon to.
        @return      : A Tk-compatible PhotoImage.
        '''
        icon = Image.open(path)
        icon = icon.resize(size)
        return ImageTk.PhotoImage(icon)

    def _toggle_theme(self, event=None):
        '''
        Toggles between the dark and light themes defined in styles.py.

        @param  : N/A
        @return : N/A
        @raise  : N/A
        '''
        going_light = getattr(self, '_dark_mode', True)
        self._dark_mode = not going_light

        if going_light:
            colour_map = {
                styles.BG_DARK:      styles.BG_LIGHT,
                styles.TEXT_FG_DARK: styles.TEXT_FG_LIGHT,
                styles.SURFACE_DARK: styles.SURFACE_LIGHT,
            }
            styles.BG, styles.TEXT_FG, styles.SURFACE = (
                styles.BG_LIGHT, styles.TEXT_FG_LIGHT, styles.SURFACE_LIGHT)
        else:
            colour_map = {
                styles.BG_LIGHT:      styles.BG_DARK,
                styles.TEXT_FG_LIGHT: styles.TEXT_FG_DARK,
                styles.SURFACE_LIGHT: styles.SURFACE_DARK,
            }
            styles.BG, styles.TEXT_FG, styles.SURFACE = (
                styles.BG_DARK, styles.TEXT_FG_DARK, styles.SURFACE_DARK)

        def _walk(widget):
            if not getattr(widget, 'theme_locked', False):
                for option in ('bg', 'fg'):
                    try:
                        current = widget.cget(option)
                    except tk.TclError:
                        continue

                    new_colour = colour_map.get(current)
                    if new_colour:
                        try:
                            widget.configure(**{option: new_colour})
                        except tk.TclError:
                            pass
            # Swap icon variants for any themed image buttons we encounter.
            if isinstance(widget, widgets.ButtonImage):
                widget.update_theme_image(self._dark_mode)

            for child in widget.winfo_children():
                _walk(child)

        # Walking from self.root also reaches any currently-open Toplevel
        # windows (note popup, birthday popup, tooltips) since Toplevels
        # are still children of root in the widget hierarchy.
        _walk(self.root)

        # ttk widgets (the event-type Combobox, the scrollbar) don't expose
        # plain 'bg'/'fg' options, so the generic walk above skips them via
        # the TclError catch. Theme them explicitly through ttk.Style.
        style = ttk.Style()
        style.configure('TCombobox',
                         fieldbackground=styles.SURFACE,
                         background=styles.SURFACE,
                         foreground=styles.TEXT_FG)
        style.map('TCombobox',
                  fieldbackground=[('readonly', styles.SURFACE)],
                  foreground=[('readonly', styles.TEXT_FG)])
        style.configure('Vertical.TScrollbar',
                         background=styles.SURFACE,
                         troughcolor=styles.BG)

        # Note: the week grid squares themselves are untouched on purpose -
        # their colours (past/current/future/custom label/event category)
        # are semantic, not theme chrome, and should stay the same
        # regardless of light or dark mode.

    def _build_controls(self):
        '''
        The controls section which enables the user to type their birthday,
        update the week visualisation, save the custom grid and load a grid from json.
        The controls section includes 4 statistics based on how much of their life has passed.

        @param  : N/A
        @return : N/A
        @raise  : N/A
        '''
        # Container frame for the controls to maintain the grid width and left
        # align the buttons and right align the stats.
        frame = widgets.Frame(self._content, width=styles.CANVAS_WIDTH, height=100)
        frame.pack(pady=(6, 10))

        # Default birthday value.
        self.dob_var = tk.StringVar(value=datetime.today().strftime('%Y-%m-%d'))

        # Frame for the tools.
        tool_frame = widgets.Frame(frame, height=40, width=styles.CANVAS_WIDTH)
        tool_frame.pack(anchor='center', fill='x', expand=True)
        tool_frame.columnconfigure([0,4], weight=3)

        # OPEN FILE BUTTON TO IMPORT SAVED FILES
        self.open_folder_image_dark = self._load_icon(get_resource_path("icons/open_folder_darkmode.png"))
        self.open_folder_image_light = self._load_icon(get_resource_path("icons/open_folder_lightmode.png"))

        open_button = widgets.ButtonImage(
            tool_frame,
            image_dark  = self.open_folder_image_dark,
            image_light = self.open_folder_image_light,
            dark_mode   = self._dark_mode
            )
        open_button.grid(row=0, column=1, padx=5, ipadx=10, ipady=10)

        open_button.bind("<Button-1>", lambda event: self.load_data())
        open_button.bind("<Enter>", lambda event: self._show_tooltip_buttons(tooltip_text="Open file", event=event), add="+")
        open_button.bind("<Motion>", self._update_tooltip_position, add='+')
        open_button.bind("<Leave>", self._hide_tooltip_buttons, add="+")

        # SAVE VISUALISATION BUTTON
        self.save_file_image_dark = self._load_icon(get_resource_path("icons/save_file_darkmode.png"))
        self.save_file_image_light = self._load_icon(get_resource_path("icons/save_file_lightmode.png"))

        save_button = widgets.ButtonImage(
            tool_frame,
            image_dark  = self.save_file_image_dark,
            image_light = self.save_file_image_light,
            dark_mode   = self._dark_mode
            )
        save_button.grid(row=0, column=2, padx=5, ipadx=10, ipady=10)

        save_button.bind("<Button-1>", lambda event: self.save_data())
        save_button.bind("<Enter>", lambda event: self._show_tooltip_buttons(tooltip_text="Save file", event=event), add="+")
        save_button.bind("<Motion>", self._update_tooltip_position, add='+')
        save_button.bind("<Leave>", self._hide_tooltip_buttons, add="+")

        # Light and dark mode toggle.
        self.theme_icon_image_dark = self._load_icon(get_resource_path("icons/light mode.png"))
        self.theme_icon_image_light = self._load_icon(get_resource_path("icons/dark mode.png"))

        theme_button = widgets.ButtonImage(
            tool_frame,
            image_dark  = self.theme_icon_image_dark,
            image_light = self.theme_icon_image_light,
            dark_mode   = self._dark_mode
            )
        theme_button.grid(row=0, column=3, padx=5, ipadx=10, ipady=10)

        theme_button.bind("<Button-1>", lambda event: self._toggle_theme())
        theme_button.bind("<Enter>", lambda event: self._show_tooltip_buttons(tooltip_text="Toggle theme", event=event), add="+")
        theme_button.bind("<Motion>", self._update_tooltip_position, add='+')
        theme_button.bind("<Leave>", self._hide_tooltip_buttons, add="+")
        
        # Spacer
        widgets.FrameSpacerH100(frame).pack(anchor='center', fill='both', expand=True)

        # Stats about the 4000 weeks visualisation. 
        self._stat_vars: dict[str, tk.StringVar] = {}

        # The lifespace that is used to generate the grid.
        self.life_var = tk.StringVar(value='80')

        stats_frame = widgets.Frame(frame)
        stats_frame.pack(fill="both", expand=True)

        for i, key in enumerate(('Weeks Lived', 'Years Remaining', 'Life Complete')):
            # Small caption text for the type of statistic.
            widgets.CaptionLabel(stats_frame, text=key).grid(row=0, column=i, padx=40)

            # Declare the statistic variable to be populated based on the birthday.
            v = tk.StringVar(value='—')
            self._stat_vars[key] = v

            widgets.H2Label(stats_frame, textvariable=v).grid(row=1, column=i, padx=40)

        # Spacer
        widgets.FrameSpacerH100(frame).pack(anchor='center', fill='both', expand=True)

    def _build_grid(self):
        outer = widgets.Frame(self._content)
        outer.pack(pady=(0, 20))

        self.canvas = tk.Canvas(
            outer,
            bg=styles.BG,
            highlightthickness=0,
            width=styles.CANVAS_WIDTH,
            height=styles.ROWS * styles.CELL + styles.GAP
            )
        self.canvas.pack()

        self._boxes: list[list[int]] = []
        self.years_labels: list[int] = []

        for year in range(styles.ROWS):
            y_top = styles.GAP + year * styles.CELL

            # Create the row of week boxes.
            row: list[int] = []
            for week in range(styles.COLS):
                x1 = styles.YEAR_W + styles.GAP + week * styles.CELL
                rect = self.canvas.create_rectangle(
                    x1,
                    y_top,
                    x1 + styles.BOX,
                    y_top + styles.BOX,
                    fill= styles.FUTURE_COLOR,
                    outline=''
                )
                week_num = year * styles.COLS + week
                cell = widgets.Week_Cell(week_num, year, week, "past", styles.FUTURE_COLOR, rect)
                self.week_cells.append(cell)
                    
                row.append(rect)

            self._boxes.append(row)

        self.canvas.bind('<Motion>',          self._on_hover)
        self.canvas.bind('<Leave>',           self._on_leave)
        self.canvas.bind('<Button-1>',        self._open_week_popup)

    def _build_footer(self):
        footer_frame = widgets.Frame(self._content)
        footer_frame.pack(pady=(22, 50))
        widgets.CaptionLabel(footer_frame, text="Designed & Developed by Kelton Boyter-Grant").pack()

    # ── Data / rendering ──────────────────────────────────────────────────────

    def _week_start_date(self, row: int, col: int) -> date:
        '''
        Calendar date for a given (row, col) grid cell.

        Anchors each row to the real birthday + N calendar years, rather than
        assuming every year is exactly 52 * 7 = 364 days. A calendar year is
        365 (or 366) days, so naively doing
        `dob + timedelta(weeks=row * 52 + col)` drifts behind real time by
        about 1.25 days every row - roughly a month after 25 years.
        '''
        try:
            year_anchor = self._dob.replace(year=self._dob.year + row)
        except ValueError:
            # dob was Feb 29 and the target year isn't a leap year.
            year_anchor = self._dob.replace(month=2, day=28, year=self._dob.year + row)

        return year_anchor + timedelta(weeks=col)

    def _set_birthday_text(self, text:str):
        '''
        Updates the birthday label's text without the unsaved work suffix '*'.
        '''
        self._birthday_text = text
        self._refresh_birthday_label()

    def _refresh_birthday_label(self):
        '''
        Redraws the birthday label, appending '*' when there is unsaved work.
        '''

        suffix = "*" if self._dirty else ""

        self.birthday.config(text=f"{self._birthday_text}{suffix}")

    def _mark_dirty(self):
        '''
        Flags unsaved work and updates the birthday label to inform the user.
        '''
        if not self._dirty:
            self._dirty = True
            self._refresh_birthday_label()

    def _mark_clean(self):
        '''
        Flags the unsaved-work flag
        '''
        if self._dirty:
            self._dirty = False
            self._refresh_birthday_label()

    def has_unsaved_changes(self) -> bool:
        '''
        Returns the status of whether there are unsaved changes.
        Used before quitting the app to prompt the user to save.
        '''
        return self._dirty
    
    
    def _refresh(self):
        try:
            dob      = date.fromisoformat(self.dob_var.get().strip())
            life_yrs = max(1, int(self.life_var.get().strip()))
        except ValueError:
            return

        today       = date.today()
        weeks_lived = max(0, (today - dob).days // 7)
        total_weeks = life_yrs * styles.COLS
        remaining   = max(0, total_weeks - weeks_lived)
        years_left  = round(remaining / 52, 1)
        pct         = min(100.0, round(weeks_lived / total_weeks * 100, 1))

        self._stat_vars['Weeks Lived'].set(f'{weeks_lived:,}')
        self._stat_vars['Years Remaining'].set(str(years_left))
        self._stat_vars['Life Complete'].set(f'{pct}%')

        self._weeks_lived = weeks_lived
        self._total_weeks = total_weeks
        self._dob         = dob

        for year, row_boxes in enumerate(self._boxes):
            for week, rect in enumerate(row_boxes):
                n = year * styles.COLS + week
                color = self._colour_for_week(n, weeks_lived)
                self.canvas.itemconfig(rect, fill=color)

                # Keep the Week_Cell object in sync with what's on screen.
                if n < len(self.week_cells):
                    wc = self.week_cells[n]
                    wc.colour = color
                    note = self._week_notes.get(n)
                    if note:
                        wc.description = note.get('description', '')
                        wc.image_paths = list(note.get('image_paths') or [])
                        wc.category    = note.get('category', 'Select Category')

    def _colour_for_week(self, week_num: int, weeks_lived: int = None) -> str:
        '''
        Works out which colour a given week square should be, in priority order:
        1) the event category colour chosen for a saved week note.
        2) the default past / current / future colour based on the date of birth.

        @param week_num    : The week index (year * COLS + week).
        @param weeks_lived : Optionally pass a pre-computed weeks_lived to avoid recalculating.
        @return             : A hex colour string.
        '''
        if week_num in self._week_labels:
            return self._custom_labels[self._week_labels[week_num]]['color']

        note = self._week_notes.get(week_num)
        if note:
            category = note.get('category')
            if category and category in styles.event_type_colours and category != "Select Category":
                return styles.event_type_colours[category]

        if weeks_lived is None:
            weeks_lived = self._weeks_lived

        if week_num < weeks_lived - 1:
            return styles.PAST_COLOR
        elif week_num == weeks_lived - 1:
            return styles.NOW_COLOR
        else:
            return styles.FUTURE_COLOR

    def _apply_week_colour(self, week_num: int):
        '''
        Recomputes and immediately paints a single week square on the canvas,
        keeping the matching Week_Cell object's colour attribute in sync.
        Used after saving/clearing a week note so the grid updates without
        needing a full re-render of every cell.

        @param week_num : The week index (year * COLS + week).
        @return          : N/A
        '''
        row, col = divmod(week_num, styles.COLS)
        if not (0 <= row < len(self._boxes) and 0 <= col < styles.COLS):
            return

        colour = self._colour_for_week(week_num)
        rect = self._boxes[row][col]
        self.canvas.itemconfig(rect, fill=colour)

        if week_num < len(self.week_cells):
            wc = self.week_cells[week_num]
            wc.colour = colour
            note = self._week_notes.get(week_num)
            if note:
                wc.description = note.get('description', '')
                wc.image_paths = list(note.get('image_paths') or [])
                wc.category    = note.get('category', 'Select Category')
            else:
                wc.description = ''
                wc.image_paths = []
                wc.category    = 'Select Category'

    # ── Grid interaction ──────────────────────────────────────────────────────
    def _open_week_popup(self, event: tk.Event):
        if self._click_pending:
            self.root.after_cancel(self._click_pending)
            self._click_pending = None

        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        gx, gy = cx - styles.YEAR_W - styles.GAP, cy - styles.GAP
        if gx < 0 or gy < 0:
            return

        col, row = int(gx // styles.CELL), int(gy // styles.CELL)
        if not (0 <= col < styles.COLS and 0 <= row < styles.ROWS):
            return

        week_num = row * styles.COLS + col
        if week_num >= self._weeks_lived - 1:
            return

        # Only allow notes on cells with a custom label.
        self._open_note_dialog(week_num)

    def _on_hover(self, event: tk.Event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        gx = cx - styles.YEAR_W - styles.GAP
        gy = cy - styles.GAP
        if gx < 0 or gy < 0:
            self._hide_tooltip()
            return

        col = int(gx // styles.CELL)
        row = int(gy // styles.CELL)
        if not (0 <= col < styles.COLS and 0 <= row < styles.ROWS):
            self._hide_tooltip()
            return

        week_num = row * styles.COLS + col
        screen_x = self.canvas.winfo_rootx() + event.x
        screen_y = self.canvas.winfo_rooty() + event.y

        if week_num != self._tooltip_week:
            self._tooltip_week = week_num
            self._show_tooltip(week_num, screen_x, screen_y)
        elif self._tooltip_win:
            self._position_grid_tooltip(self._tooltip_win, screen_x, screen_y)

    def _on_leave(self, _=None):
        self._hide_tooltip()
        self._tooltip_week = None

    # ── Tooltip ───────────────────────────────────────────────────────────────
    # Create the buttons Tooltip
    def _show_tooltip_buttons(self, tooltip_text: str, event: tk.Event= None):
        # Hide this tooltip to prevent duplicates
        self._hide_tooltip_buttons()

        if event is None or not hasattr(event, 'x_root'):
            return

        # Get the mouse coordinates
        screen_x = event.x_root
        screen_y = event.y_root

        # Create the tooltip label
        tooltip_label = tk.Toplevel(self.root)
        tooltip_label.overrideredirect(True)
        tooltip_label.config(bg=styles.BG)
        tooltip_label.attributes('-topmost', True)

        # Create the label widget
        tooltip_border = tk.Frame(tooltip_label, bg=styles.NOW_COLOR, padx=1, pady=1)
        tooltip_border.pack()
        widgets.CaptionLabel(tooltip_border, text=tooltip_text).pack(anchor='w', ipadx=10, ipady=2)

        tooltip_label.update_idletasks()
        tooltip_label.geometry(f'+{screen_x + 20}+{screen_y + 20}')
        self._tooltip_buttons = tooltip_label

    # Update the tooltip position
    def _update_tooltip_position(self, event: tk.Event=None):
        """Updates tooltip position as the cursor moves across the widget."""
        if self._tooltip_buttons and event:
            screen_x = event.x_root
            screen_y = event.y_root
            self._tooltip_buttons.geometry(f'+{screen_x + 20}+{screen_y + 20}')

    # Destroy the buttons tooltip
    def _hide_tooltip_buttons(self, event = tk.Event):
        """Destroys the tooltip widget."""
        if self._tooltip_buttons:
            try:
                self._tooltip_buttons.destroy()
            except tk.TclError:
                pass
            self._tooltip_buttons = None

    def _position_grid_tooltip(self, win: tk.Toplevel, screen_x: int, screen_y: int):
                ''' 
                Positions the week grid tooltip relative to the mouse, fliping it
                vertically or horizontally if the tooltip would clip the screen edges.
                '''
    
                # Set the default position relative to the mouse=
                pos_x = screen_x + 20
                pos_y = screen_y + 20
                
                tooltip_width  = win.winfo_reqwidth()
                tooltip_height = win.winfo_reqheight()
    
                # Screen dims
                screen_width  = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
    
                # Flip tooltip above the mouse if it will clip with the bottom of the window
                if pos_y + tooltip_height > screen_height:
                    pos_y = screen_y - tooltip_height - 10
    
                # Shit the tooltip to the left if it will clip the right side of the window
                if pos_x + tooltip_width > screen_width:
                    pos_x = screen_x - tooltip_width - 10
    
                pos_x = max(0, pos_x)
                pos_y = max(0, pos_y)
    
                win.geometry(f'+{pos_x}+{pos_y}')

    # Grid Tooltip
    def _show_tooltip(self, week_num: int, screen_x: int, screen_y: int):
        """
        Create a small tooltip widget that follows the mouse to show week cell information.
        
        @param week_num: The week widget currently being hovered.
        @param screen_x: The mouse's x coordinate.
        @param screen_y: The mouse's y coordinate.
        """
        self._hide_tooltip()

        row, col = divmod(week_num, styles.COLS)

        try:
            week_start = self._week_start_date(row, col)
            header = f'{row} Years & {col + 1} Weeks | {week_start.strftime("%b %Y")}'
        except (AttributeError, TypeError):
            header = f'{row} years & {col + 1} weeks'

        note         = self._week_notes.get(week_num)
        has_note     = self._has_note_data(note)
        category     = note.get('category') if note else None
        has_category = bool(category and category != 'Select Category')
        desc         = None

        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.configure(bg=styles.BG)
        win.attributes('-topmost', True)

        # Define padding for the data in the week tooltip
        pad = 10

        # Week Information Label that is always shown.
        if has_note or has_category:
            week_info = widgets.BodyBoldLabel(win, text=header, anchor="w")
            week_info.pack(anchor='w', padx=pad, pady=2, fill="x")
        else:
            week_info = widgets.CaptionLabel(win, text=header, anchor="w")
            week_info.pack(anchor='w', padx=pad, pady=2, fill="x")

        # Event category swatch (colour picked from the event type combobox).
        if has_category:
            # Category name
            category_name = widgets.BodyLabel(win, text=category, anchor="w")
            category_name.pack(fill="x", anchor="n", pady=4, padx=pad)


        # Track images_frame outside the conditional block
        images_frame = None

        # Images for that week
        if has_note:
            body = widgets.Frame(win)
            body.pack(fill='x', padx=pad, pady=4)

            # Render every saved image (up to 4) as small thumbnails in a row.
            img_paths = [p for p in (note.get('image_paths') or [])
                         if p and os.path.isfile(p)]
            
            if img_paths:
                images_frame = widgets.Frame(body)
                images_frame.pack(side='left', padx=(0, 10), anchor='n')

                if week_num not in self._photo_cache:
                    thumbs = []

                    for p in img_paths[:4]:
                        try:
                            img = Image.open(p)
                            img.thumbnail((150, 150))
                            thumbs.append(ImageTk.PhotoImage(img))
                        except Exception:
                            pass

                    self._photo_cache[week_num] = thumbs

                thumbs = self._photo_cache.get(week_num, [])

                # Layout the all images in a 2 x 2 grid
                self.image_labels = []

                current_row    = 0
                current_column = 0

                for i, photo in enumerate(thumbs):
                    if i == 2:
                        current_row    = 1
                        current_column = 0

                    current_column += 1

                    image_label = widgets.BodyLabel(images_frame, image=photo)
                    image_label.image = photo
                    image_label.grid(row=current_row, column=current_column, padx=2, pady=2, sticky="s")

                    self.image_labels.append(image_label)


        # If the week already has a description. Placed under the images.
        if has_note:
            desc = note.get('description', '').strip()

            if desc:
                description_frame = widgets.Frame(win)
                description_frame.pack(fill="x", padx=pad, pady=(2, 20))

                description_label = widgets.BodyLabel(description_frame, text=desc, justify="left", anchor="w")
                description_label.pack(anchor='s', fill="x")

                # Match wraplength to week_info's calculated pixel width minus frame padding
                calc_width = week_info.winfo_reqwidth()

                # Set the description text to wrap at the calculated width for consistency with or without images.
                description_label.config(wraplength=calc_width)
                
                # Re-evaluate layout size after applying wraplength
                win.update_idletasks()

        self._position_grid_tooltip(win, screen_x, screen_y)
        self._tooltip_win = win
        self._tooltip_week = week_num

        def _update_widget_backgrounds_to_category():
            """Updates all background widgets in the popup to match the selected category type."""
            if category:
                category_colour = styles.event_type_colours.get(category, styles.PAST_COLOR)

                # label background
                win.config(bg=category_colour)

                # week information
                week_info.config(bg=category_colour)

                # Category name
                category_name.config(bg=category_colour)

                # Image row
                if body:
                    body.config(bg=category_colour)
                if images_frame:
                    images_frame.config(bg=category_colour)

                    for image_label in self.image_labels:
                        image_label.config(bg=category_colour)

                # Description
                if desc:
                    if description_frame and description_label:
                        description_frame.config(bg=category_colour)
                        description_label.config(bg=category_colour)

        _update_widget_backgrounds_to_category()

    def _hide_tooltip(self):
        if self._tooltip_win:
            try:
                self._tooltip_win.destroy()
            except tk.TclError:
                pass
            self._tooltip_win = None

    # ── Note dialog ───────────────────────────────────────────────────────────

    def _has_note_data(self, note) -> bool:
        """Helper function which returns what information a week widget has."""
        if not note:
            return False
        
        has_description  = bool(note.get('description'))
        has_images       = bool(note.get('image_paths'))
        has_category     = bool(note.get('category') and note.get('category') != 'Select Category')

        return has_description or has_images or has_category

    def update_popup_background(self, event=None):
            event_type = self.event_type_dropdown.get()

            if not event_type or event_type == "Select Category":
                new_background_colour = styles.BG
            else:
                new_background_colour = styles.event_type_colours.get(event_type, styles.BG)
    
            # Set the popup background
            self.week_note_popup.config(bg=new_background_colour)

            # Set the sub-widget backgrounds
            for widget in self.popup_widgets:
                try:
                    widget.configure(bg=new_background_colour)
                except Exception as error:
                    print(f"{widget} could not be updated: {error}")
                    pass

            # Reset the popup as the focus
            self.week_note_popup.focus_set()
            
    def _open_note_dialog(self, week_num: int):
        self._hide_tooltip()
        existing = self._week_notes.get(week_num, {})

        # Store a list of widgets that need their backgrounds to update with the event type
        self.popup_widgets = []

        row, col = divmod(week_num, styles.COLS)
        try:
            week_start = self._week_start_date(row, col)
            title_text = f'{row} years & {col + 1} weeks | {week_start.strftime("%b %Y")}'
        except (AttributeError, TypeError):
            title_text = f'{row} years & {col + 1} weeks'

        self.week_note_popup = tk.Toplevel(self.root)
        self.week_note_popup.title('Week Note')
        self.week_note_popup.configure(bg=styles.BG, padx=20, pady=20)
        self.week_note_popup.resizable(False, False)
        self.week_note_popup.grab_set()

        # Keyboard bindings
        self.week_note_popup.bind("<Button-1>", self._take_focus)

        sw, sh = self.get_screen_dims()
        self.week_note_popup.geometry(f'450x580+{(sw - 440) // 2}+{(sh - 600) // 2}')

        # Date information at the top of the popup.
        date_title = widgets.H3Label(self.week_note_popup, text=title_text)
        date_title.pack(anchor='w', pady=(0, 10))

        self.popup_widgets.append(date_title)

        # ── Event Type row ─────────────────────────────────────────────    
        self.event_type_dropdown = ttk.Combobox(
            self.week_note_popup,
            values= styles.event_types,
            state="readonly",
            font=styles.BODY
        )
        self.event_type_dropdown.set("Select Category")
        self.event_type_dropdown.pack(fill="x", anchor="n", pady=10)
        self.event_type_dropdown.bind("<<ComboboxSelected>>", self.update_popup_background)

        if existing.get("category"):
            self.event_type_dropdown.set(existing['category'])

        # ── Image row ─────────────────────────────────────────────
        img_row = widgets.Frame(self.week_note_popup)
        img_row.pack(fill='x', pady=10, anchor="n")

        self.popup_widgets.append(img_row)

        img_row.columnconfigure((0, 1, 2), weight=1)
        img_row.rowconfigure((0, 1), weight=1)

        row_height = 80

        # Create the 4 Canvas Preview widgets
        preview = tk.Canvas(
            img_row,
            bg=styles.SURFACE,
            width=1,
            height=row_height * 2,
            highlightthickness=0
        )
        preview.grid(row=0, column=0, rowspan=2, padx=(0, 5), sticky="nsew")

        preview_1 = tk.Canvas(
            img_row,
            bg=styles.SURFACE,
            width=1,
            height=row_height * 2,
            highlightthickness=0
        )
        preview_1.grid(row=0, column=1, rowspan=2, padx=5, sticky="nsew")

        preview_2 = tk.Canvas(
            img_row,
            bg=styles.SURFACE,
            width=1,
            height=row_height,
            highlightthickness=0
        )
        preview_2.grid(row=0, column=2, padx=(5, 0), pady=(0, 5), sticky="nsew")

        preview_3 = tk.Canvas(
            img_row,
            bg=styles.SURFACE,
            width=1,
            height=row_height,
            highlightthickness=0
        )
        preview_3.grid(row=1, column=2, padx=(5, 0), pady=(5, 0), sticky="nsew")

        # Store canvases in a list for clean iteration
        canvases = [preview, preview_1, preview_2, preview_3]

        # Normalize existing image path(s) into a list of up to 4 paths
        raw_paths = existing.get('image_paths') or existing.get('image_path') or []
        if isinstance(raw_paths, str):
            chosen_paths = [raw_paths]
        else:
            chosen_paths = list(raw_paths)[:4]

        photo_refs = [None] * 4
        filename_var = tk.StringVar()


        def _load_previews():
            """Renders images onto the 4 canvases, filling each canvas completely (object-fit: cover)."""
            img_row.update_idletasks()  # Forces Tkinter to compute real canvas pixel sizes

            for i, c in enumerate(canvases):
                c.delete('all')
                photo_refs[i] = None
                c.image = None

                if i < len(chosen_paths):
                    path = chosen_paths[i]
                    if path and os.path.isfile(path):
                        try:
                            cw = c.winfo_width()
                            ch = c.winfo_height()

                            # Fallbacks if called before canvas geometry finishes rendering
                            if cw <= 1 or ch <= 1:
                                cw = 120
                                ch = row_height * 2 if i < 2 else row_height

                            img = Image.open(path)

                            # ImageOps.fit scales and crops the image to fill (cw, ch) completely
                            # centering=(0.5, 0.5) crops equally from edges (centered)
                            fitted_img = ImageOps.fit(
                                img, 
                                (cw, ch), 
                                method=Image.Resampling.LANCZOS, 
                                centering=(0.5, 0.5)
                            )

                            photo = ImageTk.PhotoImage(fitted_img)
                            photo_refs[i] = photo
                            c.image = photo  # Prevent Garbage Collection

                            # Place image at canvas center
                            c.create_image(cw // 2, ch // 2, image=photo, anchor='center')
                        except Exception:
                            pass

            # Update status summary variable
            if chosen_paths:
                filename_var.set(f"{len(chosen_paths)} image(s) selected")
            else:
                filename_var.set('')


        def _pick_image():
            """Opens file dialog and updates image paths (max 4)."""
            image_paths = filedialog.askopenfilenames(
                parent=self.week_note_popup,
                title='Choose up to 4 images',
                filetypes=[
                    ('Images', '*.jpg *.jpeg *.png *.webp *.gif *.bmp'),
                    ('All files', '*.*')
                ]
            )
            if image_paths:
                chosen_paths.clear()
                chosen_paths.extend(list(image_paths)[:4])
                _load_previews()


        # Initial load of existing images
        _load_previews()

        add_images_button = widgets.ButtonText(img_row, text="Add images", command=_pick_image)
        add_images_button.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=10)

        # ── Description ───────────────────────────────────────────
        description_label = widgets.CaptionLabel(self.week_note_popup, text="Description")
        description_label.pack(anchor='w', pady=(10,5))

        self.popup_widgets.append(description_label)

        description_box = widgets.EntryMultilineBody(self.week_note_popup)
        description_box.pack(fill='x', pady=(0,10))

        if existing.get('description'):
            description_box.insert('1.0', existing['description'])

        # ── Buttons ───────────────────────────────────────────────
        btn_row = widgets.Frame(self.week_note_popup)
        btn_row.pack(fill='x', expand=True, anchor="s")
        btn_row.columnconfigure((0,1,2), weight=1)

        self.popup_widgets.append(btn_row)

        def _save(event: tk.Event = None):
            """Save the user's information to the selected week widget to be visualised."""
            desc     = description_box.get('1.0', 'end').strip()
            category = self.event_type_dropdown.get()

            # Only keep the note around if there's actually something to show.
            if desc or chosen_paths or (category and category != "Select Category"):
                self._week_notes[week_num] = {
                    'description'  : desc,
                    'image_paths'  : list(chosen_paths),
                    'category'     : category,
                }
            else:
                self._week_notes.pop(week_num, None)

            self._photo_cache.pop(week_num, None)

            # Repaint this week's square with the event category colour (or the
            # default past/current/future colour if no category was chosen) and
            # keep the Week_Cell object's metadata in sync.
            self._apply_week_colour(week_num)

            # Mark the work as dirty
            self._mark_dirty()

            # Close the popup
            self.week_note_popup.destroy()

        def _clear(event: tk.Event = None):
            """Reset the information in the popup."""
            self._week_notes.pop(week_num, None)
            self._photo_cache.pop(week_num, None)
            self.event_type_dropdown.set("Select Category")
            self.update_popup_background()

            chosen_paths.clear()
            description_box.delete('1.0', 'end')
            _load_previews()

            # Repaint the square back to its default colour immediately.
            self._apply_week_colour(week_num)

        def _close(event: tk.Event = None):
            """Close the week widget data popup."""
            self.week_note_popup.destroy()

        cancel_popup_button = widgets.ButtonText(btn_row, text="Cancel", command=_close)
        cancel_popup_button.grid(row=0, column=0, sticky='nsew')

        clear_popup_button = widgets.ButtonText(btn_row, text="Clear", command=_clear) 
        clear_popup_button.grid(row=0, column=1, sticky='nsew', padx=10)

        save_popup_button = widgets.ButtonTextActive(btn_row, text="Save", command=_save)
        save_popup_button.grid(row=0, column=2, sticky='nsew')

        # Now that every themed widget has been created and registered in
        # popup_widgets, apply the background colour for any pre-existing
        # category (e.g. reopening a week that was already saved).
        self.update_popup_background()

        # Set the category combobox in focus
        self.event_type_dropdown.focus_set()

        # Bind keyboard shortcuts for the popup
        self.week_note_popup.bind("<Control-Return>", _save)
        self.week_note_popup.bind("<Escape>", _close)
        self.week_note_popup.bind("<Control-space>", _clear)

    # ── Update Birthday ───────────────────────────────────────────────────────────

    def centre_launch_popup(self, root_window, popup_window, window_width, window_height):
        # Get the current position of the window
        root_x = root_window.winfo_x()
        root_y = root_window.winfo_y()

        # Get the current window width and height
        root_width = root_window.winfo_width()
        root_height = root_window.winfo_height()
        
        # Calculate the exact offsets to center the popup
        x_coord = int(root_x + (root_width - window_width) / 2)
        y_coord = int(root_y + (root_height - window_height) / 2)
        
        # Apply the geometry string (coordinates must be integers)
        popup_window.geometry(f"{window_width}x{window_height}+{x_coord}+{y_coord}")

    def create_popup(self, parent_widget, title="", width=260, height=150):
        '''
        Create a popup above the main window in the center.
        '''
        main_window = parent_widget.winfo_toplevel()

        popup = tk.Toplevel(main_window)
        popup.title(title)
        popup.resizable(False, False)
        popup.config(padx=15, pady=15, bg=styles.BG)

        popup.bind("<Button-1>", self._take_focus)

        # Launch the popup in the centre of the root window.
        self.centre_launch_popup(main_window, popup, width, height)
        
        # Make the popup modal (blocks interaction with main window)
        popup.transient(parent_widget)   
        popup.grab_set()

        return popup

    def highlight_background(self, event=None):
        ''' Update the background colour to indicate hovering. '''
        if event and event.widget:
            event.widget.config(bg = styles.SURFACE)

    def reset_background(self, event=None):
        ''' Update the background colour to the default. '''
        if event and event.widget:
            event.widget.config(bg = styles.BG)

    def open_birthday_popup(self, event=None):
        '''
        When the user clicks on the birthday label, open a popup where the
        user can type a new birthday date to visualise.
        '''
        popup = self.create_popup(self.root, "Update Birthday", 400, 150)

        # Create a label for what the user has to input.
        lbl_name = widgets.BodyLabel(popup, text="Birthday (DD-MM-YYYY)")
        lbl_name.grid(row=0, column=0, sticky="w", pady=(0,20))

        # Format the user text into XX-XX-XXXX as they are typing into the entry widget
        def format_date(user_string: str, date_entry_widget):
            digit_user_string = ""

            # Filter non-digit characters
            for char in user_string.get():
                if char.isdigit():
                    digit_user_string += char


            # Keep the input to a length of 8
            digit_user_string = digit_user_string[:8]

            # Format the input to XX-XX-XXXX
            formatted_date = ""

            if len(digit_user_string) > 0:
                formatted_date += digit_user_string[:2]
            if len(digit_user_string) >= 3:
                formatted_date += "-" + digit_user_string[2:4]
            if len(digit_user_string) >= 5:
                formatted_date += "-" + digit_user_string[4:8]

            # Set the value of the entry widget with the new format
            user_string.set(formatted_date)

            # Move the cursor to the end
            date_entry_widget.after_idle(lambda: date_entry_widget.icursor("end"))


        # User string variable to perform date formatting on
        user_date = tk.StringVar()

        # Create an entry widget 
        ent_name = widgets.EntrySingleLineBody(popup, textvariable=user_date)
        ent_name.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0,20))
        ent_name.focus_set()

        # Listen to when the user date is updated by the user to run the date formatting
        user_date.trace_add("write", lambda *args: format_date(user_date, ent_name))

        # If the user confirms try and update the swatch label
        def update_name(event=None):
            birthday = ent_name.get().strip()
            
            if not birthday:
                messagebox.showwarning("Warning", "Please enter a birthday!", parent=popup)
                return

            # Validate the birthday - expects DD-MM-YYYY as labelled on the field.
            try:
                parsed = datetime.strptime(birthday, "%d-%m-%Y").date()
            except ValueError as error:
                print(error)
                messagebox.showwarning(
                    "Warning",
                    "Please enter the birthday as DD-MM-YYYY, e.g. 15-10-1998.",
                    parent=popup)
                return

            if parsed > date.today():
                messagebox.showwarning(
                    "Warning",
                    "Birthday can't be in the future.",
                    parent=popup)
                return

            # Update birthday label (shown as entered) and the internal ISO
            # value used for all of the date maths / grid rendering.
            try:
                self._set_birthday_text(parsed.strftime("%d-%m-%Y"))
                self.dob_var.set(parsed.isoformat())
                self._refresh()
            except ValueError:
                messagebox.showwarning("Warning", "Could not update birthday, please try again.", parent=self.root)
                return

            # Mark the app as dirty
            self._mark_dirty()

            popup.destroy()
        
        def close_popup(event=None):
            popup.destroy()

        # CONFIRM AND CLOSE BUTTON
        btn_frame = widgets.Frame(popup)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="sew", pady=(20,0))
        btn_frame.columnconfigure(0, weight=1)

        btn_close = widgets.ButtonText(btn_frame, text="Cancel", command=popup.destroy)
        btn_close.grid(row=0, column=1, padx=(0,5))

        btn_create = widgets.ButtonTextActive(btn_frame, text="Update", command=update_name)
        btn_create.grid(row=0, column=2, padx=(5,0))

        # Bind keyboard inputs
        popup.bind("<Escape>", close_popup)
        popup.bind("<Return>", update_name)

    # ── Save / Load ───────────────────────────────────────────────────────────

    def save_data(self, event=None):
        """Write the added data to a JSON file with the extension .week """
        path = None

        # Check if we already have a file path to save to. If the user opened a file.
        if self.active_file_path is None:
            # Open the file dialog and ask the user to specify the path the save the data to.
            path = filedialog.asksaveasfilename(
                defaultextension='.week',
                filetypes=[
                    ('Week files', '*.week'),
                    ('JSON files', '*.json'),
                    ('All files', '*.*')
                    ],
                title='Save visualisation',
            )

            if not path:
                return
        else:
            path = self.active_file_path

        save_dir   = os.path.dirname(os.path.abspath(path))
        assets_dir = os.path.join(save_dir, '_assets')

        serialised_notes = {}
        for wn, note in self._week_notes.items():
            entry = {
                'description' : note.get('description', ''),
                'category'    : note.get('category', 'Select Category'),
            }

            img_sources = note.get('image_paths') or []
            rel_paths   = []
            for i, img_src in enumerate(img_sources[:4]):
                if img_src and os.path.isfile(img_src):
                    os.makedirs(assets_dir, exist_ok=True)
                    ext      = os.path.splitext(img_src)[1]
                    dst_name = f'week_{wn}_{i}{ext}'
                    dst_path = os.path.join(assets_dir, dst_name)

                    # Skip the copy if the image already lives at the
                    # destination (e.g. this save was loaded and the user
                    # is re-saving without changing that image). Copying a
                    # file onto itself can raise PermissionError on Windows
                    # (WinError 32) - Python 3.12+ routes same-drive copies
                    # through the native CopyFile2 API, which doesn't allow
                    # overwriting a file with itself.
                    src_abs = os.path.normcase(os.path.normpath(os.path.abspath(img_src)))
                    dst_abs = os.path.normcase(os.path.normpath(os.path.abspath(dst_path)))
                    if src_abs != dst_abs:
                        shutil.copy2(img_src, dst_path)

                    rel_paths.append(os.path.join('_assets', dst_name))

            entry['image_paths'] = rel_paths
            serialised_notes[str(wn)] = entry

        payload = {
            'birthdate':       self.dob_var.get().strip(),
            'life_expectancy': self.life_var.get().strip(),
            'custom_labels':   self._custom_labels,
            'week_labels':     {str(k): v for k, v in self._week_labels.items()},
            'week_notes':      serialised_notes,
        }

        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)
        except Exception as error:
            messagebox.showerror("Error", f"Something went wrong {error}", parent=self.root)
            return
        
        # Mark the app as not dirty
        self._mark_clean()

    def load_data(self, event=None):
        """Load the selected JSON file and update the grid visualisation."""
        path = filedialog.askopenfilename(
            filetypes=[
                ('Week files', '*.week'),
                ('JSON files', '*.json'), 
                ('All files', '*.*')
                ],
            title='Load visualisation',
        )
        if not path:
            return

        with open(path, 'r', encoding='utf-8') as f:
            payload = json.load(f)

        self.dob_var.set(payload.get('birthdate', ''))
        self.life_var.set(payload.get('life_expectancy', '80'))
        self._custom_labels = payload.get('custom_labels', [])
        self._week_labels   = {int(k): v for k, v in
                               payload.get('week_labels', {}).items()}

        json_dir = os.path.dirname(os.path.abspath(path))
        self._week_notes = {}
        for wn_str, note in payload.get('week_notes', {}).items():
            entry = {
                'description' : note.get('description', ''),
                'category'    : note.get('category', 'Select Category'),
            }

            # Support both the new multi-image key and the legacy single-image key.
            rel_paths = note.get('image_paths')
            if rel_paths is None:
                legacy = note.get('image_path')
                rel_paths = [legacy] if legacy else []

            abs_paths = []
            for rel_path in rel_paths:
                if not rel_path:
                    continue
                abs_path = os.path.join(json_dir, rel_path)
                if os.path.isfile(abs_path):
                    abs_paths.append(abs_path)
            entry['image_paths'] = abs_paths

            self._week_notes[int(wn_str)] = entry

        self._photo_cache.clear()
        self._refresh()

        # Update the date heading
        self._set_birthday_text(self._dob.strftime("%d-%m-%Y"))

        # With the data successfully loaded, set the active file path
        self.active_file_path = path


def main():

    def on_closing():
        '''
        Open a popup when use clicks the window close button to confirm if they do want to quit the app.
        '''
        if weeks_app.has_unsaved_changes():
            if messagebox.askokcancel("Quit", "Do you want to close the app? All unsaved weeks will be lost!"):
                root.destroy()
        else:
            root.destroy()

    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.iconbitmap(get_resource_path("icons/app_icon.ico"))

    root.icon = tk.PhotoImage(file=get_resource_path("icons/app_icon.png"))
    root.iconphoto(True, root.icon)

    weeks_app = App(root)
    root.mainloop()


if __name__ == '__main__':
    main()