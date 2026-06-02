import tkinter as tk
from tkinter import ttk
from datetime import date

# ── Grid constants ────────────────────────────────────────────────────────────
ROWS   = 80          # max years rendered
COLS   = 52          # weeks per year
BOX    = 15          # box size in pixels
GAP    = 3           # gap between boxes
CELL   = BOX + GAP   # 18 px per cell
YEAR_W = 32          # left column reserved for year labels

# ── Colour palette ────────────────────────────────────────────────────────────
BG           = '#0f0f0f'
PAST_COLOR   = '#4a90e2'
NOW_COLOR    = '#f5a623'
FUTURE_COLOR = '#252525'
BEYOND_COLOR = '#181818'   # weeks beyond stated life expectancy
TEXT_FG      = '#ffffff'
DIM_FG       = '#777777'
ACCENT       = '#4a90e2'
ENTRY_BG     = '#1e1e1e'


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("4000 Weeks")
        self.root.configure(bg=BG)
        self._center(1200, 576)
        self._build_ui()
        self._refresh()

    # ── Window setup ─────────────────────────────────────────────────────────

    def _center(self, w: int, h: int):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f'{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}')
        self.root.minsize(w, h)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_controls()
        self._build_stats()
        self._build_legend()
        self._build_grid()

    def _build_header(self):
        f = tk.Frame(self.root, bg=BG)
        f.pack(fill='x', padx=30, pady=(22, 2))
        tk.Label(f, text="4,000 Weeks", bg=BG, fg=TEXT_FG,
                 font=('Arial', 50, 'bold')).pack(side='left')

    def _build_controls(self):
        f = tk.Frame(self.root, bg=BG)
        f.pack(fill='x', padx=30, pady=(6, 10))

        def entry(label, var, width):
            tk.Label(f, text=label, bg=BG, fg=DIM_FG,
                     font=('Arial', 10)).pack(side='left', padx=(0, 5))
            e = tk.Entry(f, textvariable=var, width=width, bg=ENTRY_BG,
                         fg=TEXT_FG, insertbackground=TEXT_FG,
                         relief='flat', font=('Arial', 10))
            e.pack(side='left', padx=(0, 18), ipady=3)
            e.bind('<Return>', lambda _: self._refresh())

        self.dob_var  = tk.StringVar(value='1998-10-15')
        self.life_var = tk.StringVar(value='80')
        entry("Born (YYYY-MM-DD):", self.dob_var,  12)

        tk.Button(f, text="Update", command=self._refresh,
                  bg=ACCENT, fg='white', relief='flat', cursor='hand2',
                  font=('Arial', 10, 'bold'), padx=14, pady=3).pack(side='left')

    def _build_stats(self):
        f = tk.Frame(self.root, bg=BG)
        f.pack(fill='x', padx=30, pady=(0, 10))
        self._stat_vars: dict[str, tk.StringVar] = {}
        for key in ('Weeks lived', 'Weeks remaining', 'Years left', 'Life complete'):
            col = tk.Frame(f, bg=BG)
            col.pack(side='left', padx=(0, 34))
            tk.Label(col, text=key, bg=BG, fg=DIM_FG,
                     font=('Arial', 9)).pack(anchor='w')
            v = tk.StringVar(value='—')
            self._stat_vars[key] = v
            tk.Label(col, textvariable=v, bg=BG, fg=TEXT_FG,
                     font=('Arial', 15, 'bold')).pack(anchor='w')

    def _build_legend(self):
        f = tk.Frame(self.root, bg=BG)
        f.pack(fill='x', padx=30, pady=(0, 8))
        for color, label in (
            (PAST_COLOR,   'Past weeks'),
            (NOW_COLOR,    'Current week'),
            (FUTURE_COLOR, 'Future weeks'),
        ):
            dot = tk.Canvas(f, width=10, height=10, bg=BG, highlightthickness=0)
            dot.create_rectangle(0, 0, 10, 10, fill=color, outline='')
            dot.pack(side='left', padx=(0, 5))
            tk.Label(f, text=label, bg=BG, fg=DIM_FG,
                     font=('Arial', 9)).pack(side='left', padx=(0, 18))

    def _build_grid(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill='both', expand=True, padx=30, pady=(0, 20))

        vbar = ttk.Scrollbar(outer, orient='vertical')
        vbar.pack(side='right', fill='y')

        canvas_w = YEAR_W + COLS * CELL + GAP
        canvas_h = ROWS * CELL + GAP

        self.canvas = tk.Canvas(outer, bg=BG, highlightthickness=0,
                                width=canvas_w, yscrollcommand=vbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        vbar.config(command=self.canvas.yview)
        self.canvas.config(scrollregion=(0, 0, canvas_w, canvas_h))

        self.canvas.bind('<MouseWheel>',
                         lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), 'units'))

        # Draw year labels and week rectangles
        self._boxes: list[list[int]] = []
        for year in range(ROWS):
            y_top = GAP + year * CELL
            if year % 5 == 0:
                self.canvas.create_text(
                    YEAR_W - 4, y_top + BOX // 2,
                    text=str(year), anchor='e',
                    fill=DIM_FG, font=('Arial', 7),
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

        # Tooltip
        self._tooltip = self.canvas.create_text(0, 0, text='', anchor='nw',
                                                fill=TEXT_FG, font=('Arial', 8),
                                                state='hidden')
        self.canvas.tag_raise(self._tooltip)
        self.canvas.bind('<Motion>',  self._on_hover)
        self.canvas.bind('<Leave>',   self._on_leave)

    # ── Data / rendering ──────────────────────────────────────────────────────

    def _refresh(self):
        try:
            dob       = date.fromisoformat(self.dob_var.get().strip())
            life_yrs  = max(1, int(self.life_var.get().strip()))
        except ValueError:
            return

        today         = date.today()
        weeks_lived   = max(0, (today - dob).days // 7)
        total_weeks   = life_yrs * COLS
        remaining     = max(0, total_weeks - weeks_lived)
        years_left    = round(remaining / 52, 1)
        pct           = min(100.0, round(weeks_lived / total_weeks * 100, 1))

        self._stat_vars['Weeks lived'].set(f'{weeks_lived:,}')
        self._stat_vars['Weeks remaining'].set(f'{remaining:,}')
        self._stat_vars['Years left'].set(str(years_left))
        self._stat_vars['Life complete'].set(f'{pct}%')

        self._weeks_lived  = weeks_lived
        self._total_weeks  = total_weeks
        self._dob          = dob

        for year, row in enumerate(self._boxes):
            for week, rect in enumerate(row):
                n = year * COLS + week
                if n < weeks_lived - 1:
                    color = PAST_COLOR
                elif n == weeks_lived - 1:
                    color = NOW_COLOR
                elif n >= total_weeks:
                    color = BEYOND_COLOR
                else:
                    color = FUTURE_COLOR
                self.canvas.itemconfig(rect, fill=color)

    def _on_hover(self, event: tk.Event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        # Determine which cell the pointer is over
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

        # Compute approximate date for this week
        week_num = row * COLS + col
        try:
            from datetime import timedelta
            week_start = self._dob + timedelta(weeks=week_num)
            tip = f'Age {row}y w{col + 1}  ·  ~{week_start.strftime("%b %Y")}'
        except AttributeError:
            tip = f'Year {row}, week {col + 1}'

        # Position tooltip just below and right of cursor
        tx = cx + 12
        ty = cy + 12
        self.canvas.coords(self._tooltip, tx, ty)
        self.canvas.itemconfig(self._tooltip, text=tip, state='normal')
        self.canvas.tag_raise(self._tooltip)

    def _on_leave(self, _=None):
        self.canvas.itemconfig(self._tooltip, state='hidden')


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
