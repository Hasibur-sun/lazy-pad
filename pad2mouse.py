"""
lazy-pad - control your whole laptop with a gamepad (Switch Pro, clones, Xbox, PS...).

Install:   pip install pygame pynput
Run:       python pad2mouse.py
Stop:      Ctrl+C in the terminal  (or hold HOME + both stick clicks for 1s)

DEFAULT MAPPING (SDL "Xbox-style" names; on a Nintendo layout the physical
A/B and X/Y swap places - if clicks feel backwards, change SWAP_AB below):
  Left stick ........ move mouse        (LT = slow/precise, RT = fast)
  Right stick ....... move mouse, slower (hold X + right stick = scroll)
  A (bottom) ........ left click   (hold = drag)
  B (right) ......... right click
  X ................. middle click
  Y ................. Enter
  D-pad ............. arrow keys (auto-repeat when held)
  L / R shoulder .... volume down / up (auto-repeat)
  Left stick click .. mute
  Right stick click . Alt+Tab (hold Alt for 1 press) -> switch window
  Start ............. play / pause media
  Back (-/Share) .... Escape
  Guide (Home) ...... Windows/Super key
"""
import os
import sys
import time

# keep receiving controller input while another window has focus
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"
os.environ["SDL_HIDAPI_JOYSTICK"] = "1"

import pygame
from pygame._sdl2 import controller as sdl_controller
from pynput.keyboard import Controller as Keyboard, Key
from pynput.mouse import Button, Controller as Mouse

# ---------- tweakable settings ----------
SWAP_AB = False          # True if left/right click feel swapped for you
DEADZONE = 0.18          # ignore tiny stick drift (clones drift a lot)
MOUSE_SPEED = 650.0      # pixels/second at full LEFT stick (lower = slower)
RIGHT_STICK_FACTOR = 0.5 # right stick speed relative to left (0.5 = half)
SLOW_FACTOR = 0.25       # while holding LT
FAST_FACTOR = 2.5        # while holding RT
SCROLL_SPEED = 25.0      # scroll "clicks"/second at full stick
REPEAT_DELAY = 0.35      # seconds before key auto-repeat starts
REPEAT_RATE = 0.07       # seconds between repeats
CURVE = 2.0              # >1 = finer control near centre
POLL_HZ = 120
# ----------------------------------------

mouse = Mouse()
kb = Keyboard()

C = pygame
BTN = {
    "a": C.CONTROLLER_BUTTON_A, "b": C.CONTROLLER_BUTTON_B,
    "x": C.CONTROLLER_BUTTON_X, "y": C.CONTROLLER_BUTTON_Y,
    "back": C.CONTROLLER_BUTTON_BACK, "guide": C.CONTROLLER_BUTTON_GUIDE,
    "start": C.CONTROLLER_BUTTON_START,
    "ls": C.CONTROLLER_BUTTON_LEFTSTICK, "rs": C.CONTROLLER_BUTTON_RIGHTSTICK,
    "lb": C.CONTROLLER_BUTTON_LEFTSHOULDER, "rb": C.CONTROLLER_BUTTON_RIGHTSHOULDER,
    "up": C.CONTROLLER_BUTTON_DPAD_UP, "down": C.CONTROLLER_BUTTON_DPAD_DOWN,
    "left": C.CONTROLLER_BUTTON_DPAD_LEFT, "right": C.CONTROLLER_BUTTON_DPAD_RIGHT,
}
AX = {
    "lx": C.CONTROLLER_AXIS_LEFTX, "ly": C.CONTROLLER_AXIS_LEFTY,
    "rx": C.CONTROLLER_AXIS_RIGHTX, "ry": C.CONTROLLER_AXIS_RIGHTY,
    "lt": C.CONTROLLER_AXIS_TRIGGERLEFT, "rt": C.CONTROLLER_AXIS_TRIGGERRIGHT,
}

# buttons that tap a key and auto-repeat while held
REPEAT_KEYS = {
    "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
    "lb": Key.media_volume_down, "rb": Key.media_volume_up,
}
# buttons that tap a key once per press
TAP_KEYS = {
    "y": Key.enter, "back": Key.esc, "guide": Key.cmd,
    "start": Key.media_play_pause, "ls": Key.media_volume_mute,
}


def find_pad():
    """Wait until a controller is connected, then return it."""
    while True:
        pygame.event.pump()
        for i in range(pygame.joystick.get_count()):
            if sdl_controller.is_controller(i):
                pad = sdl_controller.Controller(i)
                print(f"Connected: {pad.name}")
                return pad
        print("No controller found - pair it in Bluetooth settings "
              "(waiting)...")
        time.sleep(2)


def axis(pad, name):
    v = pad.get_axis(AX[name]) / 32767.0
    return max(-1.0, min(1.0, v))


def shape(v):
    """Deadzone + response curve, keeps sign."""
    a = abs(v)
    if a < DEADZONE:
        return 0.0
    a = (a - DEADZONE) / (1.0 - DEADZONE)
    a = a ** CURVE
    return a if v > 0 else -a


def alt_tab():
    with kb.pressed(Key.alt):
        kb.tap(Key.tab)


def main():
    # init only what we need (full pygame.init() also starts audio, which
    # can hang on some laptops / Bluetooth audio setups)
    pygame.display.init()
    pygame.joystick.init()
    sdl_controller.init()
    pad = find_pad()

    left_btn = "b" if SWAP_AB else "a"
    right_btn = "a" if SWAP_AB else "b"

    held = {k: False for k in BTN}
    next_repeat = {}
    mouse_down = False
    rmouse_down = False
    px = py = sx = sy = 0.0   # sub-pixel accumulators
    last = time.perf_counter()
    quit_since = None

    print("Running. Ctrl+C to stop.")
    while True:
        try:
            pygame.event.pump()
            if not pad.attached():
                print("Controller disconnected.")
                pad = find_pad()
                continue

            now = time.perf_counter()
            dt = now - last
            last = now

            # --- mouse movement ---
            speed = MOUSE_SPEED
            if axis(pad, "lt") > 0.4:
                speed *= SLOW_FACTOR
            if axis(pad, "rt") > 0.4:
                speed *= FAST_FACTOR
            px += shape(axis(pad, "lx")) * speed * dt
            py += shape(axis(pad, "ly")) * speed * dt

            scroll_mode = bool(pad.get_button(BTN["x"]))
            if not scroll_mode:
                # right stick = slower mouse movement
                px += shape(axis(pad, "rx")) * speed * RIGHT_STICK_FACTOR * dt
                py += shape(axis(pad, "ry")) * speed * RIGHT_STICK_FACTOR * dt
            dx, dy = int(px), int(py)
            if dx or dy:
                mouse.move(dx, dy)
                px -= dx
                py -= dy

            # --- scrolling: hold X and push the right stick ---
            if scroll_mode:
                sx += shape(axis(pad, "rx")) * SCROLL_SPEED * dt
                sy += -shape(axis(pad, "ry")) * SCROLL_SPEED * dt
                cx, cy = int(sx), int(sy)
                if cx or cy:
                    mouse.scroll(cx, cy)
                    sx -= cx
                    sy -= cy

            # --- buttons ---
            for name, code in BTN.items():
                down = bool(pad.get_button(code))
                was = held[name]
                held[name] = down

                if name == left_btn:
                    if down and not mouse_down:
                        mouse.press(Button.left); mouse_down = True
                    elif not down and mouse_down:
                        mouse.release(Button.left); mouse_down = False
                elif name == right_btn:
                    if down and not rmouse_down:
                        mouse.press(Button.right); rmouse_down = True
                    elif not down and rmouse_down:
                        mouse.release(Button.right); rmouse_down = False
                elif name == "rs" and down and not was:
                    alt_tab()
                elif name in TAP_KEYS and down and not was:
                    kb.tap(TAP_KEYS[name])
                elif name in REPEAT_KEYS:
                    if down and not was:
                        kb.tap(REPEAT_KEYS[name])
                        next_repeat[name] = now + REPEAT_DELAY
                    elif down and now >= next_repeat.get(name, 0):
                        kb.tap(REPEAT_KEYS[name])
                        next_repeat[name] = now + REPEAT_RATE

            # --- emergency quit: Home + both stick clicks for 1s ---
            if held["guide"] and held["ls"] and held["rs"]:
                quit_since = quit_since or now
                if now - quit_since > 1.0:
                    print("Quit combo pressed. Bye!")
                    break
            else:
                quit_since = None

            time.sleep(1.0 / POLL_HZ)
        except KeyboardInterrupt:
            break

    if mouse_down:
        mouse.release(Button.left)
    if rmouse_down:
        mouse.release(Button.right)


if __name__ == "__main__":
    sys.exit(main())
