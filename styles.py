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
PAST_COLOR    = '#8e8e93'
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

# ── Event Types ────────────────────────────────────────────────────────────────
event_types = [
    "Select Category",
    "Activities",
    "Travel",
    "Education",
    "Career",
    "Relationships",
    "Health",
    "Family",
    "Other"]

event_type_colours = {
    "Select Category": BG,
    "Activities"     : ORANGE,
    "Travel"         : PURPLE,
    "Education"      : BLUE,
    "Career"         : GREEN,
    "Relationships"  : PINK,
    "Health"         : POLLEN,
    "Family"         : LILAC,
    "Other"          : STONE
}


# ── Font sizes ────────────────────────────────────────────────────────────────
H1        = ('Futura Cyrillic Bold',   50)
H2        = ('Futura Cyrillic Medium', 36)
H3        = ('Futura Cyrillic Medium', 20)
BODY      = ('Futura Cyrillic Book',   12)
BODY_BOLD = ('Futura Cyrillic Bold', 12)
LABEL     = ('Futura Cyrillic Book',  10)