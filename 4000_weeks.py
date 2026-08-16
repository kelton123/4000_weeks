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


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("4000 Weeks")
        self.root.configure(bg=styles.BG)
        self._center(960, 540)
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

        self._build_ui()
        self._refresh()
        self.root.after(50, self._fix_scrollregion)

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

    def _toggle_theme(self):
        '''
        First-pass light/dark mode toggle. Walks every widget under the root
        window and swaps any background/foreground colour that matches the
        "old" theme's colours for the equivalent colour in the "new" theme.
        This is a generic approach so we don't have to individually track
        every label/frame that gets created throughout the UI.

        @param  : N/A
        @return : N/A
        @raise  : N/A
        '''
        if getattr(self, '_dark_mode', True):
            # Switching TO light mode.
            colour_map = {
                styles.BG:           '#f2f2f7',
                styles.FUTURE_COLOR: '#d1d1d6',
                styles.TEXT_FG:      '#1c1c1e',
            }
            self._dark_mode = False
        else:
            # Switching back TO dark mode.
            colour_map = {
                '#f2f2f7': styles.BG,
                '#d1d1d6': styles.FUTURE_COLOR,
                '#1c1c1e': styles.TEXT_FG,
            }
            self._dark_mode = True

        def _walk(widget):
            for option in ('bg', 'fg', 'background', 'foreground'):
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
            for child in widget.winfo_children():
                _walk(child)

        _walk(self.root)

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
        self.open_folder_image = self._load_icon("icons/open_white.png")

        open_button = widgets.ButtonImage(tool_frame, image=self.open_folder_image)
        open_button.grid(row=0, column=1, padx=5, ipadx=10, ipady=10)

        open_button.bind("<Button-1>", lambda event: self.load_data())
        open_button.bind("<Enter>", lambda event: self._show_tooltip_buttons(tooltip_text="Open file", event=event), add="+")
        open_button.bind("<Motion>", self._update_tooltip_position, add='+')
        open_button.bind("<Leave>", self._hide_tooltip_buttons, add="+")

        # SAVE VISUALISATION BUTTON
        self.save_icon_image = self._load_icon("icons/save_white.png")

        save_button = widgets.ButtonImage(tool_frame, image=self.save_icon_image)
        save_button.grid(row=0, column=2, padx=5, ipadx=10, ipady=10)

        save_button.bind("<Button-1>", lambda event: self.save_data())
        save_button.bind("<Enter>", lambda event: self._show_tooltip_buttons(tooltip_text="Save file", event=event), add="+")
        save_button.bind("<Motion>", self._update_tooltip_position, add='+')
        save_button.bind("<Leave>", self._hide_tooltip_buttons, add="+")

        # Light and dark mode toggle.
        self.theme_icon_image = self._load_icon("icons/light mode.png")

        theme_button = widgets.ButtonImage(tool_frame, image=self.theme_icon_image)
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

        # Update the year labels
        birth_year = int(self.dob_var.get()[0:4])
        for i, label_id in enumerate(self.years_labels):
            self.canvas.itemconfig(label_id, text= str(birth_year + (5*i)))

    def _colour_for_week(self, week_num: int, weeks_lived: int = None) -> str:
        '''
        Works out which colour a given week square should be, in priority order:
        1) an explicit custom legend label assigned to the week.
        2) the event category colour chosen for a saved week note.
        3) the default past / current / future colour based on the date of birth.

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
            self._tooltip_win.geometry(f'+{screen_x + 14}+{screen_y + 14}')

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
        if self._tooltip_buttons:
            try:
                self._tooltip_buttons.destroy()
            except tk.TclError:
                pass
            self._tooltip_buttons = None

    # Grid Tooltip
    def _show_tooltip(self, week_num: int, screen_x: int, screen_y: int):
        self._hide_tooltip()

        row, col = divmod(week_num, styles.COLS)
        try:
            week_start = self._dob + timedelta(weeks=week_num)
            header = f'{row} Years & {col + 1} Weeks | {week_start.strftime("%b %Y")}'
        except (AttributeError, TypeError):
            header = f'{row} years & {col + 1} weeks'

        note        = self._week_notes.get(week_num)
        has_note    = self._has_note_data(note)
        category    = note.get('category') if note else None
        has_category = bool(category and category != 'Select Category')

        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.configure(bg=styles.BG)
        win.attributes('-topmost', True)

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
                            img.thumbnail((100, 100))
                            thumbs.append(ImageTk.PhotoImage(img))
                        except Exception:
                            pass
                    self._photo_cache[week_num] = thumbs

                thumbs = self._photo_cache.get(week_num, [])

                # Layout the all images in a row
                self.image_labels = []
                for i, photo in enumerate(thumbs):
                    image_label = widgets.BodyLabel(images_frame, image=photo)
                    image_label.image = photo
                    image_label.grid(row=0, column=i, padx=2, pady=2, sticky="s")

                    self.image_labels.append(image_label)


            # If the week already has a description. Placed under the images.
            desc = note.get('description', '').strip()
            if desc:
                description_frame = widgets.Frame(win)
                description_frame.pack(fill="x", padx=pad, pady=(2, 20))

                description_label = widgets.BodyLabel(description_frame, text=desc, justify="left", anchor="w")
                description_label.pack(anchor='s', fill="x")

                # Update wraplength dynamically when images_frame is rendered/resized
                if images_frame:
                    images_frame.bind(
                        "<Configure>", 
                        lambda event: description_label.config(wraplength=event.width)
                    )
                else:
                    # Fallback: Wrap to description_frame width if there are no images
                    description_frame.bind(
                        "<Configure>", 
                        lambda event: description_label.config(wraplength=event.width)
                    )

        win.update_idletasks()
        win.geometry(f'+{screen_x + 20}+{screen_y + 20}')
        self._tooltip_win = win

        def _update_widget_backgrounds_to_category():
            if category:
                category_colour = styles.event_type_colours.get(category, styles.PAST_COLOR)

                # label background
                win.config(bg=category_colour)

                # week information
                week_info.config(bg=category_colour)

                # Category name
                category_name.config(bg=category_colour)

                # Image row
                body.config(bg=category_colour)
                images_frame.config(bg=category_colour)

                for image_label in self.image_labels:
                    image_label.config(bg=category_colour)

                # Description
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
        if not note:
            return False
        has_description = bool(note.get('description'))
        has_images       = bool(note.get('image_paths'))
        has_category     = bool(note.get('category') and note.get('category') != 'Select Category')
        return has_description or has_images or has_category

    def update_popup_background(self, event=None):
            event_type = self.event_type_dropdown.get()
            new_background_colour = styles.event_type_colours[event_type]
    
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
            week_start = self._dob + timedelta(weeks=week_num)
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
            bg=styles.FUTURE_COLOR,
            width=1,
            height=row_height * 2,
            highlightthickness=0
        )
        preview.grid(row=0, column=0, rowspan=2, padx=(0, 5), sticky="nsew")

        preview_1 = tk.Canvas(
            img_row,
            bg=styles.FUTURE_COLOR,
            width=1,
            height=row_height * 2,
            highlightthickness=0
        )
        preview_1.grid(row=0, column=1, rowspan=2, padx=5, sticky="nsew")

        preview_2 = tk.Canvas(
            img_row,
            bg=styles.FUTURE_COLOR,
            width=1,
            height=row_height,
            highlightthickness=0
        )
        preview_2.grid(row=0, column=2, padx=(5, 0), pady=(0, 5), sticky="nsew")

        preview_3 = tk.Canvas(
            img_row,
            bg=styles.FUTURE_COLOR,
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

            # Close the popup
            self.week_note_popup.destroy()

        def _clear(event: tk.Event = None):
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
        self.week_note_popup.bind("<Return>", _save)
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
            event.widget.config(bg = styles.FUTURE_COLOR)

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

        # Create an entry widget 
        ent_name = widgets.EntrySingleLineBody(popup)
        ent_name.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0,20))
        ent_name.focus_set()

        # If the user confirms try and update the swatch label
        def update_name(event=None):
            birthday = ent_name.get().strip()
            if not birthday:
                messagebox.showwarning("Warning", "Please enter a birthday!", parent=popup)
                return

            # Validate the birthday - expects DD-MM-YYYY as labelled on the field.
            try:
                parsed = datetime.strptime(birthday, "%d-%m-%Y").date()
            except ValueError:
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
                self.birthday.config(text=parsed.strftime("%d-%m-%Y"))
                self.dob_var.set(parsed.isoformat())
                self._refresh()
            except ValueError:
                messagebox.showwarning("Warning", "Could not update birthday, please try again.", parent=self.root)
                return
                
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
                    shutil.copy2(img_src, os.path.join(assets_dir, dst_name))
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


def main():
    root = tk.Tk()

    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()