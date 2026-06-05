import json
import random
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import date, timedelta

# ── Grid constants ────────────────────────────────────────────────────────────
ROWS   = 80          # max years rendered
COLS   = 52          # weeks per year
BOX    = 15          # box size in pixels
GAP    = 5           # gap between boxes
CELL   = BOX + GAP   # 20 px per cell
YEAR_W = 30          # left column reserved for year labels
CANVAS_WIDTH = YEAR_W + COLS * CELL + GAP

# ── Colour palette ────────────────────────────────────────────────────────────
BG            = '#121212'
PAST_COLOR    = '#8e8e93'
NOW_COLOR     = '#ffd500'
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
H1    = 42
H2    = 33
H3    = 26
BODY  = 16
LABEL = 13


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("4000 Weeks")
        self.root.configure(bg=BG)
        self._center(960, 540)
        self.root.state("zoomed")

        # ── Runtime state ─────────────────────────────────────────
        self._custom_labels: list[dict] = []      # [{name, color}, …]
        self._week_labels:   dict[int, int] = {}  # week_num → label index

        self._weeks_lived = 0
        self._total_weeks = 0
        self._dob         = None

        self._build_ui()
        self._refresh()
        self.root.after(50, self._fix_scrollregion)

    # ── Window setup ──────────────────────────────────────────────────────────

    def _center(self, w: int, h: int):
        sw, sh = self.get_screen_dims()
        self.root.geometry(f'{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}')
        self.root.minsize(w, h)

    def get_screen_dims(self) -> tuple:
        return self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    # ── Page-level scroll container ───────────────────────────────────────────

    def _build_ui(self):
        vbar = ttk.Scrollbar(self.root, orient='vertical')
        vbar.pack(side='right', fill='y')

        self._page = tk.Canvas(self.root, bg=BG, highlightthickness=0,
                               yscrollcommand=vbar.set)
        self._page.pack(side='left', fill='both', expand=True)
        vbar.config(command=self._page.yview)

        self._content = tk.Frame(self._page, bg=BG)
        self._win_id  = self._page.create_window(0, 0, anchor='nw',
                                                  window=self._content)

        self._page.bind('<Configure>',    self._on_page_resize)
        self._content.bind('<Configure>', self._on_content_resize)
        self.root.bind_all('<MouseWheel>', self._scroll)

        self._build_header()
        self._build_controls()
        self._build_legend()
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
        frame = tk.Frame(self._content, width=CANVAS_WIDTH, height=80, bg=BG)
        frame.pack(pady=(22, 2))
        frame.pack_propagate(False)
        tk.Label(frame, text="4000 Weeks", bg=BG, fg=TEXT_FG,
                 font=('Arial', H1, 'bold')).pack()

    def _build_controls(self):
        frame = tk.Frame(self._content, bg=BG, width=CANVAS_WIDTH, height=100)
        frame.pack(pady=(6, 10))
        frame.pack_propagate(False)

        tk.Label(frame, text="Born ", bg=BG, fg=TEXT_FG,
                 font=('Arial', BODY)).pack(side='left', padx=(0, 5))

        self.dob_var = tk.StringVar(value='1998-10-15')
        birthday_entry = tk.Entry(
            frame, textvariable=self.dob_var,
            bg=FUTURE_COLOR, fg=TEXT_FG, insertbackground=TEXT_FG,
            relief='flat', font=('Arial', BODY), width=0,
        )
        birthday_entry.pack(side='left', padx=(0, 10), ipady=3, ipadx=5)
        birthday_entry.bind('<Return>', lambda _: self._refresh())

        tk.Button(frame, text="Update", command=self._refresh,
                  bg=FUTURE_COLOR, fg='white', relief='flat', cursor='hand2',
                  font=('Arial', LABEL, 'bold'), pady=2).pack(side='left', padx=10)

        tk.Button(frame, text="Load", command=self.load_data,
                  bg=FUTURE_COLOR, fg='white', relief='flat', cursor='hand2',
                  font=('Arial', LABEL, 'bold'), pady=2).pack(side='left', padx=10, ipadx=10)

        tk.Button(frame, text="Save", command=self.save_data,
                  bg=FUTURE_COLOR, fg='white', relief='flat', cursor='hand2',
                  font=('Arial', LABEL, 'bold'), pady=2).pack(side='left', padx=10, ipadx=10)

        # Spacer pushes stats to the right
        tk.Frame(frame, bg=BG).pack(side='left', fill='both', expand=True)

        self._stat_vars: dict[str, tk.StringVar] = {}
        self.life_var = tk.StringVar(value='80')
        for key in ('Weeks lived', 'Weeks left', 'Years left', 'Life complete'):
            col = tk.Frame(frame, bg=BG)
            col.pack(side='left', padx=(30, 0))
            tk.Label(col, text=key, bg=BG, fg=TEXT_FG,
                     font=('Arial', LABEL)).pack(anchor='w')
            v = tk.StringVar(value='—')
            self._stat_vars[key] = v
            tk.Label(col, textvariable=v, bg=BG, fg=TEXT_FG,
                     font=('Arial', BODY, 'bold')).pack(anchor='w')

    def _build_legend(self):
        self._legend_frame = tk.Frame(self._content, bg=BG, width=CANVAS_WIDTH)
        self._legend_frame.pack(pady=(0, 8))
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
            side='left', padx=(0, 10))

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

        used_colors = {lbl['color'].lower() for lbl in self._custom_labels}
        used_colors |= {PAST_COLOR.lower(), NOW_COLOR.lower(), FUTURE_COLOR.lower()}
        available = [c for c in PALETTE if c.lower() not in used_colors]
        if not available:
            messagebox.showwarning("No colours left",
                                   "All palette colours are already in use.")
            return

        color = random.choice(available)
        self._custom_labels.append({'name': name, 'color': color})
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

        canvas_w = YEAR_W + COLS * CELL + GAP
        canvas_h = ROWS * CELL + GAP

        self.canvas = tk.Canvas(outer, bg=BG, highlightthickness=0,
                                width=canvas_w, height=canvas_h)
        self.canvas.pack()

        self._boxes: list[list[int]] = []
        for year in range(ROWS):
            y_top = GAP + year * CELL
            if year % 5 == 0:
                self.canvas.create_text(
                    YEAR_W - 30, y_top + BOX // 2,
                    text=str(year), anchor='w',
                    fill=TEXT_FG, font=('Arial', LABEL),
                )
            row: list[int] = []
            for week in range(COLS):
                x1 = YEAR_W + GAP + week * CELL
                rect = self.canvas.create_rectangle(
                    x1, y_top, x1 + BOX, y_top + BOX,
                    fill=FUTURE_COLOR, outline='',
                )
                row.append(rect)
            self._boxes.append(row)

        self._tooltip = self.canvas.create_text(0, 0, text='', anchor='nw',
                                                fill=TEXT_FG, font=('Arial', LABEL),
                                                state='hidden')
        self.canvas.tag_raise(self._tooltip)
        self.canvas.bind('<Motion>',   self._on_hover)
        self.canvas.bind('<Leave>',    self._on_leave)
        self.canvas.bind('<Button-1>', self._on_click)

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

        today        = date.today()
        weeks_lived  = max(0, (today - dob).days // 7)
        total_weeks  = life_yrs * COLS
        remaining    = max(0, total_weeks - weeks_lived)
        years_left   = round(remaining / 52, 1)
        pct          = min(100.0, round(weeks_lived / total_weeks * 100, 1))

        self._stat_vars['Weeks lived'].set(f'{weeks_lived:,}')
        self._stat_vars['Weeks left'].set(f'{remaining:,}')
        self._stat_vars['Years left'].set(str(years_left))
        self._stat_vars['Life complete'].set(f'{pct}%')

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

    # ── Grid interaction ──────────────────────────────────────────────────────

    def _on_click(self, event: tk.Event):
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

    def _on_hover(self, event: tk.Event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        gx = cx - YEAR_W - GAP
        gy = cy - GAP
        if gx < 0 or gy < 0:
            self.canvas.itemconfig(self._tooltip, state='hidden')
            return

        col = int(gx // CELL)
        row = int(gy // CELL)
        if not (0 <= col < COLS and 0 <= row < ROWS):
            self.canvas.itemconfig(self._tooltip, state='hidden')
            return

        week_num = row * COLS + col
        try:
            week_start = self._dob + timedelta(weeks=week_num)
            tip = f'Age {row}y w{col + 1}  ·  ~{week_start.strftime("%b %Y")}'
            if week_num in self._week_labels:
                tip += f'  ·  {self._custom_labels[self._week_labels[week_num]]["name"]}'
        except (AttributeError, TypeError):
            tip = f'Year {row}, week {col + 1}'

        self.canvas.coords(self._tooltip, cx + 12, cy + 12)
        self.canvas.itemconfig(self._tooltip, text=tip, state='normal')
        self.canvas.tag_raise(self._tooltip)

    def _on_leave(self, _=None):
        self.canvas.itemconfig(self._tooltip, state='hidden')

    # ── Save / Load ───────────────────────────────────────────────────────────

    def save_data(self):
        path = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
            title='Save visualisation',
        )
        if not path:
            return

        payload = {
            'birthdate':       self.dob_var.get().strip(),
            'life_expectancy': self.life_var.get().strip(),
            'custom_labels':   self._custom_labels,
            'week_labels':     {str(k): v for k, v in self._week_labels.items()},
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

        self._rebuild_legend()
        self._refresh()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
