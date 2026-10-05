'''
THE CONSTANT STYLES FOR THE 4000 WEEKS PROGRAM.
'''

# ── Grid constants ────────────────────────────────────────────────────────────
ROWS          = 81          # max years rendered
COLS          = 52          # weeks per year
BOX           = 15          # box size in pixels
GAP           = 4           # gap between boxes
CELL          = BOX + GAP   # 20 px per cell
YEAR_W        = 30          # left column reserved for year labels
CANVAS_WIDTH  = YEAR_W + COLS * CELL + GAP + YEAR_W

# ── Colour palette ────────────────────────────────────────────────────────────

# Dark Mode Theme
BG            = '#121212'
PAST_COLOR    = "#b0b0b7"
NOW_COLOR     = '#ffffff'
FUTURE_COLOR  = '#3a3a3c'
TEXT_FG       = '#f2f2f7'

# "Surface" colour: the neutral background used by secondary/interactive
SURFACE       = FUTURE_COLOR

# Named aliases for the dark-mode values above, so the theme toggle can
# always find its way back to "dark" regardless of what BG/TEXT_FG/SURFACE
# currently hold.
BG_DARK       = BG
TEXT_FG_DARK  = TEXT_FG
SURFACE_DARK  = SURFACE

# Light Mode Theme
BG_LIGHT      = "#f2f2f7"
TEXT_FG_LIGHT = "#121212"
SURFACE_LIGHT = "#e1e1e6"

# "Accent" colours: for elements that should draw attention and stay the
# same regardless of theme (e.g. a primary/active button), rather than
# tracking the live BG/TEXT_FG swap the toggle performs. Fixed to the
# dark-mode NOW_COLOR/BG pairing so it always reads clearly.
ACCENT        = NOW_COLOR
ACCENT_FG     = BG_DARK


# Label Colours
BLUE_COBALT   = "#477e9d"
RED           = "#d91d2a"
ULTRA_VIOLET  = "#7157be"
MIDNIGHT_BLUE = "#6084bf"
DARK_OLIVE    = "#72ad6b"
APRICOT       = "#fc7450"
HARVEST_GOLD  = "#ecb620"

PALETTE = [
    RED, 
    APRICOT,
    BLUE_COBALT,
    MIDNIGHT_BLUE,
    ULTRA_VIOLET,
    DARK_OLIVE,
]

DEFAULT_LABEL_COLOURS = [
    (PAST_COLOR,  'Past'),
    (NOW_COLOR,   'Current'),
    (FUTURE_COLOR,'Future'),
]

# ── Event Types ────────────────────────────────────────────────────────────────
event_types = [
    "Select Category",
    "Career",
    "Relationships",
    "Leisure",
    "Study",
    "Travel",
    "Other"
    ]

event_type_colours = {
    "Select Category": BG,
    "Career"         : MIDNIGHT_BLUE,
    "Relationships"  : RED,
    "Leisure"        : HARVEST_GOLD,
    "Study"          : DARK_OLIVE,
    "Travel"         : ULTRA_VIOLET,
    "Other"          : APRICOT
}


# ── Font sizes ────────────────────────────────────────────────────────────────
H1        = ('Futura Cyrillic Bold',   50)
H2        = ('Futura Cyrillic Medium', 36)
H3        = ('Futura Cyrillic Medium', 20)
BODY      = ('Futura Cyrillic Book',   12)
BODY_BOLD = ('Futura Cyrillic Bold', 12)
LABEL     = ('Futura Cyrillic Book',  10)