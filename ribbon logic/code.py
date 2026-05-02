# rwet final, ribbon logic
# adafruit qualia esp32-s3 + 2.1" 480x480 round TTL RGB display
# uses 1 btn on A0 + GND, press for a completely fresh poem

# form 0: stanza (house of dust cascade, markov phrases)
# form 1: circle (words placed in a ring around the display)
# form 2: concrete (diamond shape using spacing)

# markov chain built from corpus.py at boot
# seed words come from semantic vocabulary pools by temp

import time
import math
import board
import displayio
import terminalio
import random
import digitalio
from adafruit_display_text import label
import adafruit_qualia.displays.round21 as round_display

from corpus import CORPUS_TEXT
from vocabulary import (
    COOL_MATERIAL, COOL_STRUCTURE, COOL_POWER, COOL_INTERFACE,
    COOL_LOCATION, COOL_INHABITANT, COOL_PROMISE,
    NEUTRAL_MATERIAL, NEUTRAL_STRUCTURE, NEUTRAL_POWER, NEUTRAL_INTERFACE,
    NEUTRAL_LOCATION, NEUTRAL_INHABITANT, NEUTRAL_PROMISE,
    WARM_MATERIAL, WARM_STRUCTURE, WARM_POWER, WARM_INTERFACE,
    WARM_LOCATION, WARM_INHABITANT, WARM_PROMISE,
)

# display setup
qualia = round_display.Round21()
qualia.init(auto_refresh=False)
display = qualia.display

WIDTH = 480
HEIGHT = 480
CX = WIDTH // 2
CY = HEIGHT // 2

# button setup
btn = digitalio.DigitalInOut(board.A0)
btn.direction = digitalio.Direction.INPUT
btn.pull = digitalio.Pull.UP

# state
TEMPS = ["COOL", "NEUTRAL", "WARM"]
temp_index = 1
current_form = 0

# vocabulary pools
POOLS = {
    "COOL": {
        "material":   COOL_MATERIAL,
        "structure":  COOL_STRUCTURE,
        "power":      COOL_POWER,
        "interface":  COOL_INTERFACE,
        "location":   COOL_LOCATION,
        "inhabitant": COOL_INHABITANT,
        "promise":    COOL_PROMISE,
    },
    "NEUTRAL": {
        "material":   NEUTRAL_MATERIAL,
        "structure":  NEUTRAL_STRUCTURE,
        "power":      NEUTRAL_POWER,
        "interface":  NEUTRAL_INTERFACE,
        "location":   NEUTRAL_LOCATION,
        "inhabitant": NEUTRAL_INHABITANT,
        "promise":    NEUTRAL_PROMISE,
    },
    "WARM": {
        "material":   WARM_MATERIAL,
        "structure":  WARM_STRUCTURE,
        "power":      WARM_POWER,
        "interface":  WARM_INTERFACE,
        "location":   WARM_LOCATION,
        "inhabitant": WARM_INHABITANT,
        "promise":    WARM_PROMISE,
    },
}

# build bigram markov chain from corpus
print("building markov chain...")
_words = CORPUS_TEXT.lower().split()
_chain = {}
for i in range(len(_words) - 1):
    w = _words[i]
    n = _words[i + 1]
    if w not in _chain:
        _chain[w] = []
    _chain[w].append(n)
print(f"markov ready, {len(_chain)} keys")

def markov_phrase(seed, length=3):
    seed = seed.lower().strip()
    if seed not in _chain:
        return seed
    result = [seed]
    current = seed
    for _ in range(length - 1):
        if current in _chain and _chain[current]:
            current = random.choice(_chain[current])
            current = current.rstrip(".,;:!?")
            result.append(current)
        else:
            break
    return " ".join(result)

def pick_seed(temp, slot_name):
    pool = POOLS[temp][slot_name]
    word = random.choice(pool) if pool else "soft"
    return word.split()[0]

def slot(temp, slot_name, length=3):
    seed = pick_seed(temp, slot_name)
    return markov_phrase(seed, length)

# poem generators

def poem_stanza(temp):
    m  = slot(temp, "material", 2)
    s  = slot(temp, "structure", 3)
    p  = slot(temp, "power", 3)
    i  = slot(temp, "interface", 3)
    l  = slot(temp, "location", 3)
    n  = slot(temp, "inhabitant", 3)
    pr = slot(temp, "promise", 3)
    return "\n".join([
        f"a computer of {m}",
        f"  bound by {s}",
        f"    powered by {p}",
        f"      with {i}",
        f"        resting among {l}",
        f"          inhabited by {n}",
        f"            and it offers {pr}",
    ])

def poem_circle(temp):
    slots = ["material", "structure", "power", "interface", "location", "inhabitant", "promise"]
    words = [pick_seed(temp, s) for s in slots]
    center = slot(temp, "material", 2)
    return words, center

def poem_concrete(temp):
    m  = pick_seed(temp, "material")
    s  = pick_seed(temp, "structure")
    p  = pick_seed(temp, "power")
    i  = pick_seed(temp, "interface")
    l  = pick_seed(temp, "location")
    n  = pick_seed(temp, "inhabitant")
    pr = pick_seed(temp, "promise")
    return "\n".join([
        f"a computer of {m}",
        f"   {s}",
        f"      {p}",
        f"         {i}",
        f"      {l}",
        f"   {n}",
        f"{pr}",
    ])

FORM_NAMES = ["stanza", "circle", "concrete"]

def generate_fresh_poem():
    global temp_index, current_form
    temp_index = (temp_index + 1) % len(TEMPS)
    current_form = random.randint(0, 2)
    temp = TEMPS[temp_index]
    if current_form == 0:
        return ("stanza", poem_stanza(temp))
    elif current_form == 1:
        words, center = poem_circle(temp)
        return ("circle", words, center)
    else:
        return ("concrete", poem_concrete(temp))

# display group for stanza form
g_stanza = displayio.Group()
bg1 = displayio.Bitmap(WIDTH, HEIGHT, 1)
pal1 = displayio.Palette(1)
pal1[0] = 0x000000
g_stanza.append(displayio.TileGrid(bg1, pixel_shader=pal1))

stanza_lbl = label.Label(
    terminalio.FONT,
    text=" ",
    color=0xFFFFFF,
    scale=1,
    line_spacing=1.5,
)
stanza_lbl.anchor_point = (0.5, 0.5)
stanza_lbl.anchored_position = (CX, CY)
g_stanza.append(stanza_lbl)

stanza_info = label.Label(
    terminalio.FONT,
    text=" ",
    color=0x666666,
    scale=1,
)
stanza_info.anchor_point = (0.5, 1.0)
stanza_info.anchored_position = (CX, HEIGHT - 60)
g_stanza.append(stanza_info)

# display group for circle form
g_circle = displayio.Group()
bg2 = displayio.Bitmap(WIDTH, HEIGHT, 1)
pal2 = displayio.Palette(1)
pal2[0] = 0x000000
g_circle.append(displayio.TileGrid(bg2, pixel_shader=pal2))

circle_labels = []
for _ in range(7):
    lbl = label.Label(terminalio.FONT, text=" ", color=0xFFFFFF, scale=1)
    lbl.anchor_point = (0.5, 0.5)
    lbl.anchored_position = (CX, CY)
    g_circle.append(lbl)
    circle_labels.append(lbl)

center_lbl = label.Label(
    terminalio.FONT,
    text=" ",
    color=0xFFFFFF,
    scale=1,
    line_spacing=1.4,
)
center_lbl.anchor_point = (0.5, 0.5)
center_lbl.anchored_position = (CX, CY)
g_circle.append(center_lbl)

circle_info = label.Label(
    terminalio.FONT,
    text=" ",
    color=0x666666,
    scale=1,
)
circle_info.anchor_point = (0.5, 1.0)
circle_info.anchored_position = (CX, HEIGHT - 60)
g_circle.append(circle_info)

# display group for concrete form
g_concrete = displayio.Group()
bg3 = displayio.Bitmap(WIDTH, HEIGHT, 1)
pal3 = displayio.Palette(1)
pal3[0] = 0x000000
g_concrete.append(displayio.TileGrid(bg3, pixel_shader=pal3))

concrete_lbl = label.Label(
    terminalio.FONT,
    text=" ",
    color=0xFFFFFF,
    scale=1,
    line_spacing=1.6,
)
concrete_lbl.anchor_point = (0.5, 0.5)
concrete_lbl.anchored_position = (CX, CY)
g_concrete.append(concrete_lbl)

concrete_info = label.Label(
    terminalio.FONT,
    text=" ",
    color=0x666666,
    scale=1,
)
concrete_info.anchor_point = (0.5, 1.0)
concrete_info.anchored_position = (CX, HEIGHT - 60)
g_concrete.append(concrete_info)

RADIUS = 180

def render(poem_data):
    kind = poem_data[0]

    if kind == "stanza":
        stanza_lbl.text = poem_data[1]
        stanza_info.text = TEMPS[temp_index].lower()
        display.root_group = g_stanza

    elif kind == "circle":
        words = poem_data[1]
        center = poem_data[2]
        for idx, (lbl, word) in enumerate(zip(circle_labels, words)):
            angle = (2 * math.pi * idx / len(words)) - (math.pi / 2)
            x = int(CX + RADIUS * math.cos(angle))
            y = int(CY + RADIUS * math.sin(angle))
            lbl.text = word
            lbl.anchored_position = (x, y)
        center_lbl.text = f"a computer\nof {center}"
        circle_info.text = TEMPS[temp_index].lower()
        display.root_group = g_circle

    elif kind == "concrete":
        concrete_lbl.text = poem_data[1]
        concrete_info.text = TEMPS[temp_index].lower()
        display.root_group = g_concrete

    display.refresh()
    print(f"showing: {TEMPS[temp_index]} / {FORM_NAMES[current_form]}")

# boot
print("booting ribbon logic...")
first = ("stanza", poem_stanza(TEMPS[temp_index]))
render(first)
print("ready. press button on A0 for new poem.")

# main loop
DEBOUNCE_S = 0.3
last_press = 0.0

while True:
    if not btn.value:
        now = time.monotonic()
        if now - last_press > DEBOUNCE_S:
            last_press = now
            poem_data = generate_fresh_poem()
            render(poem_data)
    time.sleep(0.05)
