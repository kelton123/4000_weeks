import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta

# ── Grid constants ────────────────────────────────────────────────────────────
ROWS   = 80          # max years rendered
COLS   = 52          # weeks per year
BOX    = 15          # box size in pixels
GAP    = 5           # gap between boxes
CELL   = BOX + GAP   # 18 px per cell
YEAR_W = 32          # left column reserved for year labels

# ── Colour palette ────────────────────────────────────────────────────────────
BG           = '#121212' # done
PAST_COLOR   = '#8e8e93' # done
NOW_COLOR    = '#ffd500' # done
FUTURE_COLOR = '#3a3a3c' # done
TEXT_FG      = '#f2f2f7' # done
ENTRY_BG     = '#3a3a3c'

# ── Font sizes ────────────────────────────────────────────────────────────
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
        self._build_ui()
        self._refresh()
        # Finalise scroll region after all widgets are laid out
        self.root.after(50, self._fix_scrollregion)

    # ── Window setup ─────────────────────────────────────────────────────────

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
        self._build_stats()
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
        f = tk.Frame(self._content, bg=BG)
        f.pack(pady=(22, 2))
        tk.Label(f, text="4000 Weeks", bg=BG, fg=TEXT_FG,
                 font=('Arial', H1, 'bold')).pack()

    def _build_controls(self):
        f = tk.Frame(self._content, bg=BG)
        f.pack(pady=(6, 10))

        def entry(label, var, width):
            tk.Label(f, text=label, bg=BG, fg=TEXT_FG,
                     font=('Arial', BODY)).pack(side='left', padx=(0, 5))
            e = tk.Entry(f, textvariable=var, width=width, bg=ENTRY_BG,
                         fg=TEXT_FG, insertbackground=TEXT_FG,
                         relief='flat', font=('Arial', BODY))
            e.pack(side='left', padx=(0, 18), ipady=3)
            e.bind('<Return>', lambda _: self._refresh())

        self.dob_var  = tk.StringVar(value='1998-10-15')
        self.life_var = tk.StringVar(value='80')
        entry("Born:", self.dob_var, BODY)

        tk.Button(f, text="Update", command=self._refresh,
                  bg=FUTURE_COLOR, fg='white', relief='flat', cursor='hand2',
                  font=('Arial', LABEL, 'bold'), padx=14, pady=3).pack(side='left')

    def _build_stats(self):
        f = tk.Frame(self._content, bg=BG)
        f.pack(pady=(0, 10))
        self._stat_vars: dict[str, tk.StringVar] = {}
        for key in ('Weeks lived', 'Weeks remaining', 'Years left', 'Life complete'):
            col = tk.Frame(f, bg=BG)
            col.pack(side='left', padx=(0, 34))
            tk.Label(col, text=key, bg=BG, fg=TEXT_FG,
                     font=('Arial', LABEL)).pack(anchor='w')
            v = tk.StringVar(value='—')
            self._stat_vars[key] = v
            tk.Label(col, textvariable=v, bg=BG, fg=TEXT_FG,
                     font=('Arial', BODY, 'bold')).pack(anchor='w')

    def _build_legend(self):
        f = tk.Frame(self._content, bg=BG)
        f.pack(pady=(0, 8))
        for color, label in (
            (PAST_COLOR,   'Past weeks'),
            (NOW_COLOR,    'Current week'),
            (FUTURE_COLOR, 'Future weeks'),
        ):
            dot = tk.Canvas(f, width=10, height=10, bg=BG, highlightthickness=0)
            dot.create_rectangle(0, 0, 10, 10, fill=color, outline='')
            dot.pack(side='left', padx=(0, 5))
            tk.Label(f, text=label, bg=BG, fg=TEXT_FG,
                     font=('Arial', LABEL)).pack(side='left', padx=(0, 18))

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
                    YEAR_W - 4, y_top + BOX // 2,
                    text=str(year), anchor='e',
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
        self.canvas.bind('<Motion>', self._on_hover)
        self.canvas.bind('<Leave>',  self._on_leave)

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
        self._stat_vars['Weeks remaining'].set(f'{remaining:,}')
        self._stat_vars['Years left'].set(str(years_left))
        self._stat_vars['Life complete'].set(f'{pct}%')

        self._weeks_lived = weeks_lived
        self._total_weeks = total_weeks
        self._dob         = dob

        for year, row in enumerate(self._boxes):
            for week, rect in enumerate(row):
                n = year * COLS + week
                if n < weeks_lived - 1:
                    color = PAST_COLOR
                elif n == weeks_lived - 1:
                    color = NOW_COLOR
                else:
                    color = FUTURE_COLOR
                self.canvas.itemconfig(rect, fill=color)

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

        week_num   = row * COLS + col
        try:
            week_start = self._dob + timedelta(weeks=week_num)
            tip = f'Age {row}y w{col + 1}  ·  ~{week_start.strftime("%b %Y")}'
        except AttributeError:
            tip = f'Year {row}, week {col + 1}'

        self.canvas.coords(self._tooltip, cx + 12, cy + 12)
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
