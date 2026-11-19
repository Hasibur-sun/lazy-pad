# lazy-pad

**Your laptop, from bed. Your controller, finally useful.**

You're under the blanket, the laptop is way over there, and getting up to skip a song feels like a personal attack. lazy-pad turns any Bluetooth gamepad into a full mouse + remote for your whole computer: the desktop, the browser, YouTube, whatever. Not just games.

I built it for a no-name Switch Pro controller clone. If your computer sees it as a gamepad, it should work.

---

## What you get

| Input | Does |
|---|---|
| Left stick | Move the mouse |
| Right stick | Move the mouse, slower, for precise aiming |
| Hold **X** + right stick | Scroll |
| **A** (bottom button) | Left click, hold to drag |
| **B** (right button) | Right click |
| **Y** | Enter |
| D-pad | Arrow keys, repeats when held |
| **L / R** shoulder | Volume down / up |
| Left stick click | Mute |
| Right stick click | Alt+Tab |
| **Start** | Play / pause |
| **Back** (- / Share) | Esc |
| **Home** | Windows key |
| Hold **LT** | Slow mouse |
| Hold **RT** | Fast mouse |

Nintendo-layout controllers swap the A/B and X/Y positions compared to Xbox ones. If your clicks feel backwards, set `SWAP_AB = True` at the top of `pad2mouse.py`.

---

## Get it running (Windows, 2 minutes)

1. Install [Python 3](https://www.python.org/downloads/). Tick **"Add Python to PATH"** in the installer.
2. Download this repo (green **Code** button, then **Download ZIP**) and unzip it.
3. Open a terminal in that folder and run:
   ```
   python -m pip install -r requirements.txt
   ```
4. Pair your controller in **Settings > Bluetooth & devices**.
5. Start it:
   ```
   python pad2mouse.py
   ```

You should see `Connected: <your controller>`. Nudge the left stick and the pointer follows. Done.

If you run it before pairing, no problem, it waits and picks the controller up when it connects. If the controller goes to sleep and wakes up, it reconnects by itself too.

### Stopping it

`Ctrl+C` in the terminal, or hold **Home + both stick clicks** for one second. That one works even when there's no window.

---

## Make it start with your laptop

So you never have to open a terminal again:

1. Press `Win + R`, type `shell:startup`, hit Enter.
2. Right-click `start-lazy-pad.bat` in this repo, **Create shortcut**, and drop that shortcut into the folder that just opened.

It starts silently in the background on every login. Don't move the repo folder afterwards, or the shortcut breaks.

Careful not to run two copies at once. Two scripts fighting over one controller means a mouse that moves double speed. If that happens, end every `python.exe` / `pythonw.exe` in Task Manager and start once.

---

## Tweak it

Everything you'd want to change sits at the top of `pad2mouse.py`:

```python
SWAP_AB = False           # clicks backwards? flip this
DEADZONE = 0.18           # stick drifting on its own? raise this
MOUSE_SPEED = 650.0       # left stick speed
RIGHT_STICK_FACTOR = 0.5  # right stick speed, relative to the left
SCROLL_SPEED = 25.0
```

Want different buttons? The mapping is just a few small tables and `if` blocks in the main loop. It's short and easy to edit.

---

## Troubleshooting

**`No module named 'pygame'`**: run `python -m pip install -r requirements.txt`. Using `python -m pip` makes sure it lands in the same Python that runs the script.

**Stuck on "No controller found"**: check the controller is actually connected in Bluetooth settings, then press a button on it to wake it. Some cheap clones have separate PC / Switch modes, so try pairing again in a different mode (usually a different button combo on the pairing button).

**Pointer drifts by itself**: cheap sticks do that. Raise `DEADZONE` to 0.25 or so.

**Freezes right at startup**: update to the latest version of this repo. Older versions initialized audio, which can hang on some setups.

---

## Other systems

Built and tested on **Windows**. macOS and Linux should work too since it uses `pygame` and `pynput`, but I haven't verified them.

- **macOS**: allow your terminal under *System Settings > Privacy & Security > Accessibility*.
- **Linux**: works on X11. Wayland blocks this kind of input injection, so it won't work there.

---

## How it works

`pygame` reads the controller through SDL's standard gamepad layer (which is why so many different pads work), and `pynput` fakes real mouse and keyboard input at the OS level. That's why it controls everything, not only one window. The script is a single file of about 200 lines.

## License

MIT. Use it, break it, improve it. PRs and button-layout ideas are welcome.
