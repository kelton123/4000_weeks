import json
import os
import random
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import date, timedelta

from PIL import Image, ImageTk

# ── Grid constants ────────────────────────────────────────────────────────────
ROWS          = 81          # max years rendered
COLS          = 52          # weeks per year
BOX           = 15          # box size in pixels
GAP           = 5           # gap between boxes
CELL          = BOX + GAP   # 20 px per cell
YEAR_W        = 30          # left column reserved for year labels
CANVAS_WIDTH  = YEAR_W + COLS * CELL + GAP + YEAR_W + YEAR_W

# ── Colour palette ────────────────────────────────────────────────────────────
BG            = '#121212'
PAST_COLOR    = '#8e8e93'
NOW_COLOR     = '#ffffff'
FUTURE_COLOR  = '#3a3a3c'
TEXT_FG       = '#f2f2f7'

# Label Colours
RED           = "#d91d2a"
ORANGE        = "#ff6410"
APRICOT       = "#fc7450"
PEACH         = "#e57e5e"
POLLEN        = "#FFD25B"
FLASH_LIGHT   = "#f7ec00"
FLASH         = "#e1f322"
GREEN         = "#8DE328"
MINT          = "#aeec9d"
TURQUOISE     = "#9ed5cc"
LIGHT_BLUE    = "#6ac5dd"
BLUE          = "#1ab5fc"
ROYAL_BLUE    = "#63aeee"
LILAC         = "#c1d8fd"
MIST_BLUE     = "#b3b8a7"
AZURE         = "#879aa1"
BLUE_COBALT   = "#477e9d"
DARK_TEAL     = "#357393"
DENIM_BLUE    = "#5b83a8"
MIDNIGHT_BLUE = "#6084bf"
OCEAN_BLUE    = "#7388c7"
PURPLE        = "#997cf7"
ULTRA_VIOLET  = "#7157be"
LAVENDAR      = "#b29aa6"
PINK_SAND     = "#ffc2a9"
LIGHT_PINK    = "#f4b0aa"
PINK          = "#ff5964"
ELECTRIC_PINK = "#ff4e51"
ROSE_RED      = "#b92946"
CAMELLIA      = "#c94544"
FLAMINGO      = "#d3836A"
WALNUT        = "#b08664"
STONE         = "#af9980"
PEBBLE        = "#ad9d8e"
DARK_OLIVE    = "#8c8c76"

PALETTE = [
    RED, ORANGE, APRICOT, PEACH, POLLEN, FLASH_LIGHT, FLASH, GREEN, MINT,
    TURQUOISE, LIGHT_BLUE, BLUE, ROYAL_BLUE, LILAC, MIST_BLUE, AZURE,
    BLUE_COBALT, DARK_TEAL, DENIM_BLUE, MIDNIGHT_BLUE, OCEAN_BLUE, PURPLE,
    ULTRA_VIOLET, LAVENDAR, PINK_SAND, LIGHT_PINK, PINK, ELECTRIC_PINK,
    ROSE_RED, CAMELLIA, FLAMINGO, WALNUT, STONE, PEBBLE, DARK_OLIVE,
]

DEFAULT_LABEL_COLOURS = [
    (PAST_COLOR,  'Past'),
    (NOW_COLOR,   'Current'),
    (FUTURE_COLOR,'Future'),
]

# ── Font sizes ────────────────────────────────────────────────────────────────
H1    = ('Arial', 42, 'bold')
H2    = 33 #('Arial', 33, 'bold')
H3    = 26 # ('Arial', 26, 'bold')
BODY  = 16 #('Arial', 16, 'bold')
LABEL = 13 #('Arial', 13, 'bold')



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
            image_path  = "",
            description = ""):
        
        self.id = id
        self.year        = year
        self.week        = week
        self.label       = label
        self.colour      = colour
        self.cell        = rectangle
        
        # Optional metadata which is added by the user.
        self.image_path  = image_path
        self.description = description
        
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


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("4000 Weeks")
        self.root.configure(bg=BG)
        self._center(960, 540)
        self.root.state("zoomed")

        # ── Runtime state ─────────────────────────────────────────
        self._custom_labels : list[dict]                    = []   # [{name, color}, …]
        self._week_labels   : dict[int, int]                = {}   # week_num → label index
        self._week_notes    : dict[int, dict]               = {}   # week_num → {description, image_path}
        self._photo_cache   : dict[int, ImageTk.PhotoImage] = {}  # keeps refs alive
        self.week_cells     : list[Week_Cell]               = []

        self._weeks_lived   = 0
        self._total_weeks   = 0
        self._dob           = None
        self._click_pending = None   # after() ID for delayed single-click
        self._tooltip_win:  tk.Toplevel | None = None
        self._tooltip_week: int | None = None

        self._build_ui()
        self._refresh()
        self.root.after(50, self._fix_scrollregion)

    # ── Window setup ──────────────────────────────────────────────────────────

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
        self._page = tk.Canvas(self.root,
                               bg                   =BG,
                               highlightthickness   =0,
                               yscrollcommand       =scrollbar.set
                               )
        self._page.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self._page.yview)

        self._content = tk.Frame(self._page, bg=BG)
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
        # self._build_legend()
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
        frame = tk.Frame(self._content, width=CANVAS_WIDTH, height=80, bg=BG)
        frame.pack(pady=(22, 2))
        frame.pack_propagate(False)

        # The active birthday - default text is "Add birthday".
        self.birthday = tk.Label(frame, text="Add birthday", bg=BG, fg=TEXT_FG, font=H1)
        self.birthday.pack()

        # Bind clicking the birthday label to allow a new date to be visualised.
        self.birthday.bind("<Button-1>", lambda event: self.open_birthday_popup())

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
        frame = tk.Frame(self._content, bg=BG, width=CANVAS_WIDTH, height=100)
        frame.pack(pady=(6, 10))

        # Default birthday value.
        self.dob_var = tk.StringVar(value='1998-10-15')

        # Frame for the tools.
        tool_frame = tk.Frame(frame, bg=BG, height=40, width=CANVAS_WIDTH)
        tool_frame.pack(anchor='center', fill='x')

        # Open file button to load a visualisation from a file.
        tk.Button(tool_frame, text="Load", command=self.load_data,
                  bg=FUTURE_COLOR, fg='white', relief='flat', cursor='hand2',
                  font=('Arial', LABEL, 'bold'), pady=2).grid(row=0, column=0, padx=20, ipadx=10)

        # Save the current visualisation with all of the metadata to a file.
        tk.Button(tool_frame, text="Save", command=self.save_data,
                  bg=FUTURE_COLOR, fg='white', relief='flat', cursor='hand2',
                  font=('Arial', LABEL, 'bold'), pady=2).grid(row=0, column=1, padx=20, ipadx=10)

        # Light and dark mode toggle.
        tk.Button(
            tool_frame,
            text="Light",
            bg=FUTURE_COLOR,
            fg='white',
            relief='flat',
            cursor='hand2',
            font=('Arial', LABEL, 'bold'),
            pady=2).grid(row=0, column=2, padx=20, ipadx=10)

        # Spacer pushes stats to the right
        tk.Frame(frame, bg=BG, height=100).pack(side='left', fill='both', expand=True)

        # Stats about the 4000 weeks visualisation. 
        self._stat_vars: dict[str, tk.StringVar] = {}

        # The lifespace that is used to generate the grid.
        self.life_var = tk.StringVar(value='80')

        stats_frame = tk.Frame(frame, bg=BG)
        stats_frame.pack(fill="both", expand=True)

        for i, key in enumerate(('Weeks Lived', 'Years Remaining', 'Life Complete')):
            tk.Label(
                stats_frame,
                text=key,
                bg=BG,
                fg=TEXT_FG,
                font=('Arial', LABEL)
                ).grid(row=0, column=i, padx=40)
            
            v = tk.StringVar(value='—')

            self._stat_vars[key] = v

            tk.Label(
                stats_frame,
                textvariable=v,
                bg=BG,
                fg=TEXT_FG,
                font=('Arial', BODY, 'bold')
                ).grid(row=1, column=i, padx=40)

    def _build_legend(self):
        self._legend_frame = tk.Frame(self._content, bg= BG, width= CANVAS_WIDTH, height= 40)
        self._legend_frame.pack(pady=(0, 30))
        self._legend_frame.pack_propagate(False)
        self._label_name_var = tk.StringVar()
        self._rebuild_legend()

    def _rebuild_legend(self):
        for widget in self._legend_frame.winfo_children():
            widget.destroy()

        # Default colour entries
        for color, label in DEFAULT_LABEL_COLOURS:
            dot = tk.Canvas(self._legend_frame, width=BOX, height=BOX,
                            bg=BG, highlightthickness=0)
            dot.create_rectangle(0, 0, BOX, BOX, fill=color, outline='')
            dot.pack(side='left', padx=(0, 5))
            tk.Label(self._legend_frame, text=label, bg=BG, fg=TEXT_FG,
                     font=('Arial', LABEL)).pack(side='left', padx=(0, 18))

        # Custom label entries with × buttons
        for idx, lbl in enumerate(self._custom_labels):
            dot = tk.Canvas(self._legend_frame, width=BOX, height=BOX,
                            bg=BG, highlightthickness=0)
            dot.create_rectangle(0, 0, BOX, BOX, fill=lbl['color'], outline='')
            dot.pack(side='left', padx=(0, 4))
            tk.Label(self._legend_frame, text=lbl['name'], bg=BG, fg=TEXT_FG,
                     font=('Arial', LABEL)).pack(side='left', padx=(0, 2))
            tk.Button(self._legend_frame, text='×', bg=BG, fg=TEXT_FG,
                      relief='flat', cursor='hand2', font=('Arial', LABEL),
                      command=lambda i=idx: self._remove_custom_label(i),
                      padx=2, pady=0).pack(side='left', padx=(0, 14))

        # Divider
        tk.Frame(self._legend_frame, bg=FUTURE_COLOR, width=2, height=18).pack(
            side='left', padx=(0, 25))

        # New label entry + add button
        self._label_name_var.set('')
        tk.Entry(self._legend_frame, textvariable=self._label_name_var,
                 bg=FUTURE_COLOR, fg=TEXT_FG, insertbackground=TEXT_FG,
                 relief='flat', font=('Arial', LABEL), width=12,
                 ).pack(side='left', padx=(0, 6), ipady=2)

        tk.Button(self._legend_frame, text='+', command=self._add_custom_label,
                  bg=FUTURE_COLOR, fg='white', relief='flat', cursor='hand2',
                  font=('Arial', LABEL, 'bold'), pady=0,
                  ).pack(side='left', ipadx=4)

        self._fix_scrollregion()

    def _add_custom_label(self):
        name = self._label_name_var.get().strip()
        if not name:
            return
        used = {lbl['color'].lower() for lbl in self._custom_labels}
        used |= {PAST_COLOR.lower(), NOW_COLOR.lower(), FUTURE_COLOR.lower()}
        available = [c for c in PALETTE if c.lower() not in used]
        if not available:
            messagebox.showwarning("No colours left",
                                   "All palette colours are already in use.")
            return
        self._custom_labels.append({'name': name, 'color': random.choice(available)})
        self._rebuild_legend()

    def _remove_custom_label(self, idx: int):
        # Reset any weeks that used this label
        weeks_to_reset = [wn for wn, li in self._week_labels.items() if li == idx]
        for wn in weeks_to_reset:
            row, col = divmod(wn, COLS)
            self.canvas.itemconfig(self._boxes[row][col], fill=PAST_COLOR)
            del self._week_labels[wn]

        # Shift down indices for labels above the removed one
        self._week_labels = {
            wn: (li - 1 if li > idx else li)
            for wn, li in self._week_labels.items()
        }

        self._custom_labels.pop(idx)
        self._rebuild_legend()

    def _build_grid(self):
        outer = tk.Frame(self._content, bg=BG)
        outer.pack(pady=(0, 20))

        self.canvas = tk.Canvas(outer, bg=BG, highlightthickness=0,
                                width=CANVAS_WIDTH, height=ROWS * CELL + GAP)
        self.canvas.pack()

        self._boxes: list[list[int]] = []
        self.years_labels: list[int] = []

        for year in range(ROWS):
            y_top = GAP + year * CELL

            # Create the delta year label.
            if year % 5 == 0:
                self.canvas.create_text(
                    YEAR_W - 30,
                    y_top + BOX // 2,
                    text=str(year),
                    anchor='w',
                    fill=TEXT_FG,
                    font=('Arial', LABEL)
                )

            # Create the row of week boxes.
            row: list[int] = []
            for week in range(COLS):
                x1 = YEAR_W + GAP + week * CELL
                rect = self.canvas.create_rectangle(
                    x1,
                    y_top,
                    x1 + BOX,
                    y_top + BOX,
                    fill=FUTURE_COLOR,
                    outline=''
                )
                cell = Week_Cell((year + week), year, week, "past", FUTURE_COLOR, rect)
                self.week_cells.append(cell)
                    
                row.append(rect)
            
            # Add the year to the right of the grid
            if year % 5 == 0:
                birth_year = int(self.dob_var.get()[0:4])
                year_label = self.canvas.create_text(
                    CANVAS_WIDTH -  50,
                    y_top + BOX // 2,
                    text = str(birth_year + year),
                    anchor = 'w',
                    fill = TEXT_FG,
                    font = ('Arial', LABEL)
                )
                self.years_labels.append(year_label)

            self._boxes.append(row)

        self.canvas.bind('<Motion>',          self._on_hover)
        self.canvas.bind('<Leave>',           self._on_leave)
        self.canvas.bind('<Button-1>',        self._on_click)
        self.canvas.bind('<Double-Button-1>', self._on_double_click)

    def _build_footer(self):
        f = tk.Frame(self._content, bg=BG)
        f.pack(pady=(22, 50))
        tk.Label(f, text="Designed & Developed by Kelton Boyter-Grant",
                 bg=BG, fg=TEXT_FG, font=('Arial', LABEL)).pack()

    # ── Data / rendering ──────────────────────────────────────────────────────

    def _refresh(self):
        try:
            dob      = date.fromisoformat(self.dob_var.get().strip())
            life_yrs = max(1, int(self.life_var.get().strip()))
        except ValueError:
            return

        today       = date.today()
        weeks_lived = max(0, (today - dob).days // 7)
        total_weeks = life_yrs * COLS
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
                n = year * COLS + week
                if n in self._week_labels:
                    color = self._custom_labels[self._week_labels[n]]['color']
                elif n < weeks_lived - 1:
                    color = PAST_COLOR
                elif n == weeks_lived - 1:
                    color = NOW_COLOR
                else:
                    color = FUTURE_COLOR
                self.canvas.itemconfig(rect, fill=color)

        # Update the year labels
        birth_year = int(self.dob_var.get()[0:4])
        for i, label_id in enumerate(self.years_labels):
            self.canvas.itemconfig(label_id, text= str(birth_year + (5*i)))

    # ── Grid interaction ──────────────────────────────────────────────────────

    def _on_click(self, event: tk.Event):
        if self._click_pending:
            self.root.after_cancel(self._click_pending)
        self._click_pending = self.root.after(250, lambda: self._do_single_click(event))

    def _do_single_click(self, event: tk.Event):
        self._click_pending = None
        if not self._custom_labels:
            return

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        gx = cx - YEAR_W - GAP
        gy = cy - GAP
        if gx < 0 or gy < 0:
            return

        col = int(gx // CELL)
        row = int(gy // CELL)
        if not (0 <= col < COLS and 0 <= row < ROWS):
            return

        week_num = row * COLS + col
        if week_num >= self._weeks_lived - 1:
            return  # only past weeks

        current_idx = self._week_labels.get(week_num, -1)
        next_idx    = current_idx + 1
        rect        = self._boxes[row][col]

        if next_idx >= len(self._custom_labels):
            self._week_labels.pop(week_num, None)
            self.canvas.itemconfig(rect, fill=PAST_COLOR)
        else:
            self._week_labels[week_num] = next_idx
            self.canvas.itemconfig(rect, fill=self._custom_labels[next_idx]['color'])

        # Invalidate tooltip cache for this cell so it refreshes
        if self._tooltip_week == week_num:
            self._tooltip_week = None

    def _on_double_click(self, event: tk.Event):
        if self._click_pending:
            self.root.after_cancel(self._click_pending)
            self._click_pending = None

        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        gx, gy = cx - YEAR_W - GAP, cy - GAP
        if gx < 0 or gy < 0:
            return

        col, row = int(gx // CELL), int(gy // CELL)
        if not (0 <= col < COLS and 0 <= row < ROWS):
            return

        week_num = row * COLS + col
        if week_num >= self._weeks_lived - 1:
            return

        # Only allow notes on cells with a custom label.
        self._open_note_dialog(week_num)

    def _on_hover(self, event: tk.Event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        gx = cx - YEAR_W - GAP
        gy = cy - GAP
        if gx < 0 or gy < 0:
            self._hide_tooltip()
            return

        col = int(gx // CELL)
        row = int(gy // CELL)
        if not (0 <= col < COLS and 0 <= row < ROWS):
            self._hide_tooltip()
            return

        week_num = row * COLS + col
        screen_x = self.canvas.winfo_rootx() + event.x
        screen_y = self.canvas.winfo_rooty() + event.y

        if week_num != self._tooltip_week:
            self._tooltip_week = week_num
            self._show_tooltip(week_num, screen_x, screen_y)
        elif self._tooltip_win:
            self._tooltip_win.geometry(f'+{screen_x + 14}+{screen_y + 14}')

    def _on_leave(self, _=None):
        self._hide_tooltip()
        self._tooltip_week = None

    # ── Tooltip ───────────────────────────────────────────────────────────────

    def _show_tooltip(self, week_num: int, screen_x: int, screen_y: int):
        self._hide_tooltip()

        row, col = divmod(week_num, COLS)
        try:
            week_start = self._dob + timedelta(weeks=week_num)
            header = f'{row} years & {col + 1} weeks | {week_start.strftime("%b %Y")}'
        except (AttributeError, TypeError):
            header = f'{row} years & {col + 1} weeks'

        note        = self._week_notes.get(week_num)
        has_note    = self._has_note_data(note)
        label_entry = (self._custom_labels[self._week_labels[week_num]]
                       if week_num in self._week_labels else None)

        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.configure(bg=BG)
        win.attributes('-topmost', True)

        pad = 10

        tk.Label(win, text=header, bg=BG, fg=TEXT_FG,
                 font=('Arial', BODY)).pack(anchor='w', padx=pad, pady=(pad, 2))

        if label_entry:
            lf = tk.Frame(win, bg=BG)
            lf.pack(anchor='w', padx=pad, pady=(0, 4))
            dot = tk.Canvas(lf, width=10, height=10, bg=BG, highlightthickness=0)
            dot.create_rectangle(0, 0, 10, 10, fill=label_entry['color'], outline='')
            dot.pack(side='left', padx=(0, 5))
            tk.Label(lf, text=label_entry['name'], bg=BG, fg=TEXT_FG,
                     font=('Arial', BODY)).pack(side='left')

        if has_note:
            body = tk.Frame(win, bg=BG)
            body.pack(fill='x', padx=pad, pady=(4, pad))

            img_path = note.get('image_path')
            if img_path and os.path.isfile(img_path):
                if week_num not in self._photo_cache:
                    try:
                        img = Image.open(img_path)
                        img.thumbnail((300, 180))
                        self._photo_cache[week_num] = ImageTk.PhotoImage(img)
                    except Exception:
                        pass
                if week_num in self._photo_cache:
                    tk.Label(body, image=self._photo_cache[week_num],
                             bg=BG).pack(side='left', padx=(0, 10))

            desc = note.get('description', '').strip()
            if desc:
                tk.Label(body, text=desc, bg=BG, fg=TEXT_FG,
                         font=('Arial', BODY), wraplength=220,
                         justify='left').pack(side='left', anchor='n')
        else:
            tk.Frame(win, bg=BG, height=pad).pack()

        win.update_idletasks()
        win.geometry(f'+{screen_x + 14}+{screen_y + 14}')
        self._tooltip_win = win

    def _hide_tooltip(self):
        if self._tooltip_win:
            try:
                self._tooltip_win.destroy()
            except tk.TclError:
                pass
            self._tooltip_win = None

    # ── Note dialog ───────────────────────────────────────────────────────────

    def _has_note_data(self, note) -> bool:
        return bool(note and (note.get('description') or note.get('image_path')))
    
    def _open_note_dialog(self, week_num: int):
        self._hide_tooltip()
        existing = self._week_notes.get(week_num, {})

        row, col = divmod(week_num, COLS)
        try:
            week_start = self._dob + timedelta(weeks=week_num)
            title_text = f'Week note | {row} years & {col + 1} weeks | {week_start.strftime("%b %Y")}'
        except (AttributeError, TypeError):
            title_text = f'Week note | {row} years & {col + 1} weeks'

        dlg = tk.Toplevel(self.root)
        dlg.title('Week Note')
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()

        sw, sh = self.get_screen_dims()
        dlg.geometry(f'440x320+{(sw - 440) // 2}+{(sh - 320) // 2}')

        tk.Label(dlg, text=title_text, bg=BG, fg=TEXT_FG,
                 font=('Arial', LABEL)).pack(anchor='w', padx=16, pady=(14, 10))

        # ── Image row ─────────────────────────────────────────────
        img_row = tk.Frame(dlg, bg=BG)
        img_row.pack(fill='x', padx=16, pady=(0, 10))

        preview = tk.Canvas(img_row, width=120, height=80, bg=FUTURE_COLOR,
                            highlightthickness=0)
        preview.pack(side='left', padx=(0, 14))

        chosen_path  = [existing.get('image_path')]
        photo_ref    = [None]
        filename_var = tk.StringVar()

        def _load_preview(path):
            preview.delete('all')
            if not path or not os.path.isfile(path):
                filename_var.set('')
                return
            try:
                img = Image.open(path)
                img.thumbnail((120, 80))
                photo_ref[0] = ImageTk.PhotoImage(img)
                preview.create_image(60, 40, image=photo_ref[0], anchor='center')
                filename_var.set(os.path.basename(path))
            except Exception:
                filename_var.set('(could not load image)')

        _load_preview(chosen_path[0])

        def _pick_image():
            p = filedialog.askopenfilename(
                parent=dlg, title='Choose image',
                filetypes=[('Images', '*.jpg *.jpeg *.png *.webp *.gif *.bmp'),
                           ('All files', '*.*')])
            if p:
                chosen_path[0] = p
                _load_preview(p)

        side = tk.Frame(img_row, bg=BG)
        side.pack(side='left', anchor='n')
        tk.Button(side, text='Choose image…', command=_pick_image,
                  bg=FUTURE_COLOR, fg=TEXT_FG, relief='flat', cursor='hand2',
                  font=('Arial', LABEL)).pack(anchor='w')
        tk.Label(side, textvariable=filename_var, bg=BG, fg=TEXT_FG,
                 font=('Arial', 10), wraplength=230).pack(anchor='w', pady=(4, 0))

        # ── Description ───────────────────────────────────────────
        tk.Label(dlg, text='Description', bg=BG, fg=TEXT_FG,
                 font=('Arial', LABEL)).pack(anchor='w', padx=16)
        desc_box = tk.Text(dlg, height=4, bg=FUTURE_COLOR, fg=TEXT_FG,
                           insertbackground=TEXT_FG, relief='flat',
                           font=('Arial', LABEL), wrap='word')
        desc_box.pack(fill='x', padx=16, pady=(4, 12))
        if existing.get('description'):
            desc_box.insert('1.0', existing['description'])

        # ── Buttons ───────────────────────────────────────────────
        btn_row = tk.Frame(dlg, bg=BG)
        btn_row.pack(fill='x', padx=16, pady=(0, 16))

        def _save():
            desc = desc_box.get('1.0', 'end').strip()
            self._week_notes[week_num] = {
                'description': desc,
                'image_path':  chosen_path[0],
            }
            self._photo_cache.pop(week_num, None)
            dlg.destroy()

        def _clear():
            self._week_notes.pop(week_num, None)
            self._photo_cache.pop(week_num, None)
            dlg.destroy()

        tk.Button(btn_row, text='Save', command=_save,
                  bg=BLUE, fg='white', relief='flat', cursor='hand2',
                  font=('Arial', LABEL, 'bold'), padx=14).pack(side='left', padx=(0, 8))
        tk.Button(btn_row, text='Clear', command=_clear,
                  bg=FUTURE_COLOR, fg=TEXT_FG, relief='flat', cursor='hand2',
                  font=('Arial', LABEL), padx=14).pack(side='left', padx=(0, 8))
        tk.Button(btn_row, text='Cancel', command=dlg.destroy,
                  bg=FUTURE_COLOR, fg=TEXT_FG, relief='flat', cursor='hand2',
                  font=('Arial', LABEL), padx=14).pack(side='left')

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
        popup.config(padx=15, pady=15)

        # Launch the popup in the centre of the root window.
        self.centre_launch_popup(main_window, popup, width, height)
        
        # Make the popup modal (blocks interaction with main window)
        popup.transient(parent_widget)   
        popup.grab_set()

        return popup


    def open_birthday_popup(self, event=None):
        '''
        When the user clicks on the birthday label, open a popup where the
        user can type a new birthday date to visualise.
        '''
        popup = self.create_popup(self.root, "Update Birthday", 350, 110)

        # Create a label for what the user has to input.
        lbl_name = tk.Label(popup, text="Birthday DD-MM-YYYY:", font=("futura-book", 12))
        lbl_name.grid(row=0, column=0, sticky="w", pady=(0,20))

        # Create an entry widget 
        ent_name = tk.Entry(popup, font=("futura-book", 14))
        ent_name.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0,20))
        ent_name.focus_set()

        # If the user confirms try and update the swatch label
        def update_name(event=None):
            birthday = ent_name.get().strip()
            if not birthday:
                messagebox.showwarning("Warning", "Please enter a project name!", parent=popup)
                return
            
            # TODO: Validate birthday
            

            # Update birthday label
            try:
                self.birthday.config(text=birthday)
                self.dob_var.set(birthday)
                self._refresh()
            except ValueError:
                messagebox.showwarning("Warning", "Could not update birthday, please try again.", parent=self.root)
                return
                
            popup.destroy()
        
        def close_popup(self):
            popup.destroy()

        # Create confirm and quit buttons
        btn_frame = tk.Frame(popup)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        btn_frame.columnconfigure(0, weight=1)

        btn_close = tk.Button(
            btn_frame,
            text                = "Cancel",
            font                = ("futura-book", 12),
            command             = popup.destroy
            )
        btn_close.grid(row=0, column=1, padx=(0,5))

        btn_create = tk.Button(
            btn_frame,
            text                = "Update",
            font                = ("futura-book", 12),
            command             = update_name
            )
        btn_create.grid(row=0, column=2, padx=(5,0))

        # Bind keyboard inputs
        popup.bind("<Escape>", close_popup)
        popup.bind("<Return>", update_name)

    # ── Save / Load ───────────────────────────────────────────────────────────

    def save_data(self):
        path = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
            title='Save visualisation',
        )
        if not path:
            return

        save_dir   = os.path.dirname(os.path.abspath(path))
        assets_dir = os.path.join(save_dir, '_assets')

        serialised_notes = {}
        for wn, note in self._week_notes.items():
            entry   = {'description': note.get('description', '')}
            img_src = note.get('image_path')
            if img_src and os.path.isfile(img_src):
                os.makedirs(assets_dir, exist_ok=True)
                ext      = os.path.splitext(img_src)[1]
                dst_name = f'week_{wn}{ext}'
                shutil.copy2(img_src, os.path.join(assets_dir, dst_name))
                entry['image_path'] = os.path.join('_assets', dst_name)
            else:
                entry['image_path'] = None
            serialised_notes[str(wn)] = entry

        payload = {
            'birthdate':       self.dob_var.get().strip(),
            'life_expectancy': self.life_var.get().strip(),
            'custom_labels':   self._custom_labels,
            'week_labels':     {str(k): v for k, v in self._week_labels.items()},
            'week_notes':      serialised_notes,
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)

    def load_data(self):
        path = filedialog.askopenfilename(
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
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
            entry    = {'description': note.get('description', '')}
            rel_path = note.get('image_path')
            if rel_path:
                abs_path = os.path.join(json_dir, rel_path)
                entry['image_path'] = abs_path if os.path.isfile(abs_path) else None
            else:
                entry['image_path'] = None
            self._week_notes[int(wn_str)] = entry

        self._photo_cache.clear()
        self._rebuild_legend()
        self._refresh()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
