# ==== PART 1/2 — from file start to end of MidiRadioGroupFrame  ====
import tkinter as tk
from tkinter import ttk, filedialog
import tkinter.font as tkfont
import mido
from mido import Message
import json
import threading

# ---------------- Theme / constants ----------------
COL_BG = "#1e1e1e"
COL_FRAME = "#2e2e2e"
COL_ACCENT = "#bd6500"
COL_TEXT = "#686868"
COL_BTN_HOVER = "#444444"
COL_BTN = "#333333"
ICON_RESIZE = ""
ICON_DRAG = "."
# Placeholders — reassigned to named fonts after root is created:
ICON_FONT = ("Helvetica", 16)
COL_SLIDER_NAME = "#df4600"     # Colour for slider name entry
COL_SLIDER_VALUE = "#fc7100"    # Colour for value label
COL_BTN_DEFAULT = "#444444"     # grey when not latched
COL_BTN_LATCHED = "#ff8800"     # orange when latched
GRID_SIZE = 10
MIN_WIDTH = 50
MIN_HEIGHT = 20
# Placeholder — reassigned to named fonts after root is created:
BUTTON_FONT = ("Helvetica", 14, "bold")
BUTTON_FG = "#ffffff"
RADIO_PAD = 1

DRF_INSTANCES = []


root = tk.Tk()

# Optional global scaling (1.0 default; bump for touch screens)
try:
    root.tk.call("tk", "scaling", 1.0)
except Exception:
    pass

# ---------- Global font setup (centralized control) ----------
# Change these to re-skin the whole app:
FONT_FAMILY = "DejaVu Sans"    # e.g., "Ubuntu", "Noto Sans", "Inter", "Fira Sans"
SIZE_UI      = 13              # base UI text
SIZE_LABEL   = 13              # small labels
SIZE_HEADER  = 15              # control titles / headers
SIZE_VALUE   = 12             # small value readouts
SIZE_BUTTON  = 14              # push buttons
SIZE_RADIO   = 16              # radio group buttons (bold, bigger)
SIZE_ICON    = 18              # any icon glyphs / placeholders

# Named fonts (widgets using these update live if you tweak them)
FONT_UI     = tkfont.Font(family=FONT_FAMILY, size=SIZE_UI)
FONT_LABEL  = tkfont.Font(family=FONT_FAMILY, size=SIZE_LABEL)
FONT_HEADER = tkfont.Font(family=FONT_FAMILY, size=SIZE_HEADER, weight="bold")
FONT_VALUE  = tkfont.Font(family=FONT_FAMILY, size=SIZE_VALUE)
FONT_BUTTON = tkfont.Font(family=FONT_FAMILY, size=SIZE_BUTTON, weight="bold")
FONT_RADIO  = tkfont.Font(family=FONT_FAMILY, size=SIZE_RADIO, weight="bold")
FONT_ICON   = tkfont.Font(family=FONT_FAMILY, size=SIZE_ICON)

# Tk option database defaults (apply broadly to tk widgets)
root.option_add("*Font",              FONT_UI)
root.option_add("*Label.Font",        FONT_LABEL)
root.option_add("*Entry.Font",        FONT_UI)
root.option_add("*Button.Font",       FONT_BUTTON)
root.option_add("*Radiobutton.Font",  FONT_RADIO)
root.option_add("*Scale.Font",        FONT_UI)
root.option_add("*Menu.Font",         FONT_UI)

# Base ttk font as a safety net (some themes ignore option DB for ttk)
try:
    ttk.Style().configure(".", font=FONT_UI)
except Exception:
    pass

# Rebind globals that referenced tuples to named fonts
ICON_FONT   = FONT_ICON
BUTTON_FONT = FONT_RADIO  # used by radio buttons in your code

# Title / state
current_filename = tk.StringVar(value="blank")
root.title(f"Mid Tk - {current_filename.get()}")

root.geometry("700x777")
root.configure(bg=COL_BG)

locked = tk.BooleanVar(value=False)

output_names = mido.get_output_names()
input_names = mido.get_input_names()
print("Available MIDI inputs:", input_names)

midi_out = None
midi_in_thread = None

selected_port = tk.StringVar(value=output_names[0] if output_names else "")
selected_input_port = tk.StringVar(value=input_names[0] if input_names else "")

sliders = []
buttons = []
radio_groups = []

# ttk style (colors + font)
style = ttk.Style()
style.theme_use("default")
style.configure(
    "TCombobox",
    fieldbackground=COL_FRAME,
    background=COL_FRAME,
    foreground=COL_TEXT,
    arrowcolor=COL_ACCENT,
    selectbackground=COL_ACCENT,
    selectforeground=COL_BG,
    borderwidth=0,
    relief="flat",
    font=FONT_UI,
)
style.map(
    "TCombobox",
    fieldbackground=[("readonly", COL_FRAME)],
    background=[("active", COL_FRAME)],
    foreground=[("readonly", COL_TEXT)],
    arrowcolor=[("active", COL_ACCENT)],
)

def toggle_lock():
    locked.set(not locked.get())
    # Show/hide grips on all frames whenever lock state changes
    for fr in DRF_INSTANCES:
        fr.update_grips()
    print("Locked:", locked.get())

DEFAULT_WIDTH = MIN_WIDTH
DEFAULT_HEIGHT_SLIDER = 500
DEFAULT_HEIGHT_BUTTON = MIN_WIDTH
WIDGET_WIDTH = 60
SPAWN_GAP = 2

# Larger touch-friendly scrollbars
SCROLLBAR_WIDTH = 20  # adjust to taste

# ---------------- Canvas + Scrollbars ----------------
canvas_container = tk.Frame(root, bg=COL_BG)
canvas_container.pack(fill="both", expand=True)

# Use grid to remove the scrollbar corner
canvas_container.grid_rowconfigure(0, weight=1)
canvas_container.grid_columnconfigure(0, weight=1)

# Main canvas
canvas = tk.Canvas(canvas_container, bg=COL_BG, highlightthickness=0)
canvas.grid(row=0, column=0, sticky="nsew")

# Bind resize handler (fix: ensure embedded frame resizes with window)
def _on_canvas_configure(e):
    # Keep the embedded frame at least as large as the viewport, but prefer content size
    vw, vh = max(e.width, 1), max(e.height, 1)
    w = max(SR_W, vw + 1)
    h = max(SR_H, vh)
    canvas.itemconfig(window_id, width=w, height=h)
    canvas.configure(scrollregion=(0, 0, w, h))

canvas.bind("<Configure>", _on_canvas_configure)

# Vertical scrollbar (touch friendly size)
v_scroll = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview, width=SCROLLBAR_WIDTH)
v_scroll.grid(row=0, column=1, sticky="ns")

# Horizontal scrollbar (touch friendly size)
h_scroll = tk.Scrollbar(canvas_container, orient="horizontal", command=canvas.xview, width=SCROLLBAR_WIDTH)
h_scroll.grid(row=1, column=0, sticky="ew")

canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

# Inner frame (one window only)
scrollable_frame = tk.Frame(canvas, bg=COL_BG)
window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

# Put near your other globals
SR_W = 0   # current scrollregion width
SR_H = 0   # current scrollregion height
PADDING = 200
GROW_CHUNK = 2000  # how much extra room to add when we hit the edge

def open_radio_group_setup(radio_group):
    DIALOG_PAD  = 6           # tighter than RADIO_PAD*3
    LIST_HEIGHT = 220         # pixels; enough for ~6–8 rows comfortably

    win = tk.Toplevel(root)
    win.title("Edit MIDI Radio Group")
    win.configure(bg=COL_FRAME)
    # win.geometry("560x560")  # ❌ drop this so the dialog hugs its content
    win.resizable(False, True) # width fixed, height can grow if needed

    mode_var        = radio_group.mode
    channel_var     = radio_group.channel
    orientation_var = radio_group.orientation
    num_var         = tk.IntVar(value=len(radio_group.button_data))

    existing_controls = [int(b.get("control", 0)) for b in radio_group.button_data] or [0]
    cc_all_var = tk.StringVar(value=str(existing_controls[0]))

    entries = []

    # ---------- Top controls ----------
    top = tk.Frame(win, bg=COL_FRAME)
    top.pack(side="top", fill="x", padx=DIALOG_PAD, pady=DIALOG_PAD)

    tk.Label(top, text="MIDI Mode", bg=COL_FRAME, fg=COL_TEXT, font=FONT_LABEL)\
        .grid(row=0, column=0, sticky="w", padx=4, pady=2)
    ttk.Combobox(top, textvariable=mode_var, values=["CC", "Note", "Aftertouch"],
                 state="readonly", width=12)\
        .grid(row=0, column=1, sticky="w", padx=4, pady=2)

    tk.Label(top, text="Channel", bg=COL_FRAME, fg=COL_TEXT, font=FONT_LABEL)\
        .grid(row=1, column=0, sticky="w", padx=4, pady=2)
    ttk.Combobox(top, textvariable=channel_var, values=[str(i) for i in range(1, 17)],
                 state="readonly", width=4)\
        .grid(row=1, column=1, sticky="w", padx=4, pady=2)

    tk.Label(top, text="CC/Note", bg=COL_FRAME, fg=COL_TEXT, font=FONT_LABEL)\
        .grid(row=2, column=0, sticky="w", padx=4, pady=2)
    ttk.Combobox(top, textvariable=cc_all_var, values=[str(x) for x in range(0, 128)],
                 state="readonly", width=5)\
        .grid(row=2, column=1, sticky="w", padx=4, pady=2)

    tk.Label(top, text="Orientation", bg=COL_FRAME, fg=COL_TEXT, font=FONT_LABEL)\
        .grid(row=3, column=0, sticky="w", padx=4, pady=2)
    ttk.Combobox(top, textvariable=orientation_var, values=["vertical", "horizontal"],
                 state="readonly", width=12)\
        .grid(row=3, column=1, sticky="w", padx=4, pady=2)

    tk.Label(top, text="Number of Options", bg=COL_FRAME, fg=COL_TEXT, font=FONT_LABEL)\
        .grid(row=4, column=0, sticky="w", padx=4, pady=4)
    num_spin = tk.Spinbox(top, from_=1, to=64, textvariable=num_var, width=4, relief="flat",
                          bg=COL_BG, fg=COL_ACCENT, insertbackground=COL_ACCENT, font=FONT_UI)
    num_spin.grid(row=4, column=1, sticky="w", padx=4, pady=4)

    top.grid_columnconfigure(0, weight=0)
    top.grid_columnconfigure(1, weight=1)

    # ---------- Scrollable list (non-expanding, fixed height) ----------
    center = tk.Frame(win, bg=COL_FRAME)
    center.pack(side="top", fill="x", expand=False, padx=DIALOG_PAD, pady=(0, DIALOG_PAD))

    lst_canvas = tk.Canvas(center, bg=COL_FRAME, highlightthickness=0, height=LIST_HEIGHT)
    vsb = tk.Scrollbar(center, orient="vertical", command=lst_canvas.yview)

    list_frame = tk.Frame(lst_canvas, bg=COL_FRAME)
    list_frame.bind("<Configure>", lambda e: lst_canvas.configure(scrollregion=lst_canvas.bbox("all")))
    lst_canvas.create_window((0, 0), window=list_frame, anchor="nw")
    lst_canvas.configure(yscrollcommand=vsb.set)

    lst_canvas.pack(side="left", fill="x", expand=True)
    vsb.pack(side="right", fill="y")

    # ---------- Bottom ----------
    bottom = tk.Frame(win, bg=COL_FRAME)
    bottom.pack(side="bottom", fill="x", padx=DIALOG_PAD, pady=DIALOG_PAD)

    def bucket_mid(i: int, n: int) -> int:
        n = max(1, int(n))
        low  = (i * 128) // n
        high = ((i + 1) * 128) // n - 1
        if high < low: high = low
        return max(0, min(127, (low + high) // 2))

    def build_entries(recompute_values: bool):
        for w in list_frame.winfo_children(): w.destroy()
        entries.clear()

        try:
            n = max(1, int(num_var.get()))
        except Exception:
            n = 1

        hdr = {"bg": COL_FRAME, "fg": COL_TEXT, "font": FONT_HEADER}
        tk.Label(list_frame, text="Label", **hdr).grid(row=0, column=0, padx=4, pady=4, sticky="w")
        tk.Label(list_frame, text="Value (0–127)", **hdr).grid(row=0, column=1, padx=4, pady=4)

        keep_existing = (not recompute_values) and (n == len(radio_group.button_data))

        for i in range(n):
            label_var = tk.StringVar()
            val_var   = tk.StringVar()

            if i < len(radio_group.button_data) and keep_existing:
                bd = radio_group.button_data[i]
                label_var.set(bd.get("label", f"{i+1}"))
                val_var.set(str(int(bd.get("value", bucket_mid(i, n)))))
            else:
                label_var.set(radio_group.button_data[i]["label"] if i < len(radio_group.button_data) else f"{i+1}")
                val_var.set(str(bucket_mid(i, n)))

            tk.Entry(list_frame, textvariable=label_var, width=18,
                     bg=COL_BG, fg=COL_ACCENT, insertbackground=COL_ACCENT,
                     relief="flat", font=FONT_UI)\
                .grid(row=i+1, column=0, padx=4, pady=2, sticky="we")

            tk.Spinbox(list_frame, from_=0, to=127, textvariable=val_var, width=4, relief="flat",
                       bg=COL_BG, fg=COL_ACCENT, insertbackground=COL_ACCENT, font=FONT_UI)\
                .grid(row=i+1, column=1, padx=4, pady=2, sticky="w")

            entries.append((label_var, val_var))

        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_columnconfigure(1, weight=0)
        win.after_idle(lambda: lst_canvas.yview_moveto(0.0))

        # After filling, let the window tighten to its requested width
        win.update_idletasks()
        win.minsize(win.winfo_reqwidth(), win.winfo_reqheight())

    def apply_changes():
        shared_control = int(cc_all_var.get())
        new_data = []
        for label, val in entries:
            try: v = int(val.get())
            except ValueError: v = 0
            v = max(0, min(127, v))
            new_data.append({"label": label.get(), "control": shared_control, "value": v})

        radio_group.button_data = new_data
        radio_group.orientation.set(orientation_var.get())
        radio_group.rebuild_controls()

        if radio_group.buttons:
            sel = radio_group.selected.get()
            if not (0 <= sel < len(radio_group.buttons)):
                radio_group.selected.set(0)
            radio_group.update_visuals()
        win.destroy()

    num_spin.config(command=lambda: build_entries(recompute_values=True))
    num_var.trace_add("write", lambda *_: build_entries(recompute_values=True))

    build_entries(recompute_values=True)

    tk.Button(bottom, text="Apply", command=apply_changes,
              bg=COL_ACCENT, fg=COL_TEXT, font=FONT_BUTTON,
              relief="flat", width=10).pack(side="right")
    # Center the dialog over the main window
    win.update_idletasks()
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_w = root.winfo_width()
    root_h = root.winfo_height()
    win_w = win.winfo_width()
    win_h = win.winfo_height()

    pos_x = root_x + (root_w // 2) - (win_w // 2)
    pos_y = root_y + (root_h // 2) - (win_h // 2)

    win.geometry(f"+{pos_x}+{pos_y}")

def update_scroll_region():
    global SR_W, SR_H

    max_right = 0
    max_bottom = 0
    for child in scrollable_frame.winfo_children():
        # DraggableResizableFrame is in Part 2; we don’t import here to avoid circular refs.
        try:
            from_types = ("DraggableResizableFrame",)
            if child.winfo_class() == "Frame" and hasattr(child, "place_info"):
                pass
        except Exception:
            pass

        # Conservative approach: check geometry on any child Frame
        if isinstance(child, tk.Frame):
            child.update_idletasks()
            r = child.winfo_x() + child.winfo_width()
            b = child.winfo_y() + child.winfo_height()
            if r > max_right:  max_right = r
            if b > max_bottom: max_bottom = b

    needed_w = max_right + PADDING
    needed_h = max_bottom + PADDING

    # Ensure we always have some extra room
    vw = max(canvas.winfo_width(), 1)
    vh = max(canvas.winfo_height(), 1)

    if SR_W == 0: SR_W = vw + GROW_CHUNK
    if SR_H == 0: SR_H = vh + GROW_CHUNK

    if needed_w > SR_W - 100:
        SR_W = needed_w + GROW_CHUNK
    if needed_h > SR_H - 100:
        SR_H = needed_h + GROW_CHUNK

    # Make scrollable area and embedded frame as big as content
    w = max(SR_W, vw + 1)   # +1 ensures H scrollbar shows when larger than viewport
    h = max(SR_H, vh)       # V scrollbar logic already OK
    canvas.configure(scrollregion=(0, 0, w, h))
    canvas.itemconfig(window_id, width=w, height=h)

def _on_frame_configure(event):
    update_scroll_region()

scrollable_frame.bind("<Configure>", _on_frame_configure)

# ---- Mouse wheel bindings ----
def _on_mousewheel_windows_mac(event):
    units = -1 if event.delta > 0 else 1
    canvas.yview_scroll(units, "units")

def _on_mousewheel_linux_up(event):
    canvas.yview_scroll(-1, "units")

def _on_mousewheel_linux_down(event):
    canvas.yview_scroll(1, "units")

def _on_shift_wheel(event):
    step = -1 if getattr(event, "delta", 0) > 0 else 1
    canvas.xview_scroll(step, "units")

def _bind_wheels(_):
    canvas.bind_all("<MouseWheel>", _on_mousewheel_windows_mac)   # Win/Mac
    canvas.bind_all("<Button-4>", _on_mousewheel_linux_up)        # Linux
    canvas.bind_all("<Button-5>", _on_mousewheel_linux_down)      # Linux
    canvas.bind_all("<Shift-MouseWheel>", _on_shift_wheel)

def _unbind_wheels(_):
    canvas.unbind_all("<MouseWheel>")
    canvas.unbind_all("<Button-4>")
    canvas.unbind_all("<Button-5>")
    canvas.unbind_all("<Shift-MouseWheel>")

canvas.bind("<Enter>", _bind_wheels)
canvas.bind("<Leave>", _unbind_wheels)

def _safe_bg_menu(event):
    try:
        show_background_menu(event)  # defined in Part 2
    except NameError:
        pass

canvas.bind("<Button-3>", _safe_bg_menu)
scrollable_frame.bind("<Button-3>", _safe_bg_menu)

# Early scrollregion init
root.after_idle(update_scroll_region)

# ---------------- Helpers ----------------
def get_spawn_geometry(widget_list, fallback_height):
    try:
        if widget_list:
            last_widget = widget_list[-1]["frame"] if isinstance(widget_list[-1], dict) else widget_list[-1].master
            last_widget.update_idletasks()
            last_x = int(last_widget.winfo_x())
            last_y = int(last_widget.winfo_y())
            last_width = int(last_widget.winfo_width())
            x = last_x + last_width + SPAWN_GAP
            y = last_y
        else:
            raise Exception
    except Exception:
        # Safe on-canvas defaults for first spawn
        x, y = 10, 10

    x = max(0, round(x / GRID_SIZE) * GRID_SIZE)
    y = max(0, round(y / GRID_SIZE) * GRID_SIZE)
    return x, y, DEFAULT_WIDTH, fallback_height

class SliderProxy:
    def __init__(self, slider_entry):
        self.slider_entry = slider_entry
    def get_state(self):
        return slider_state(self.slider_entry)

# ---------------- Widgets ----------------
class MidiButtonFrame(tk.Frame):
    def __init__(self, master, state=None):
        super().__init__(master, bg=COL_FRAME)

        self.name = tk.StringVar(value=state["name"] if state else "?")
        self.mode = tk.StringVar(value=state["mode"] if state else "CC")
        self.channel = tk.StringVar(value=str(state["channel"]) if state else "1")
        self.control = tk.StringVar(value=str(state["control"]) if state else "1")
        self.latch_mode = tk.BooleanVar(value=state["latch"] if state else False)

        self.latched = state.get("latched", False) if state else False
        self.value_on = 127
        self.value_off = 0

        self.button = tk.Button(
            self,
            text=self.name.get(),
            bg=COL_BTN_DEFAULT,
            fg=COL_TEXT,
            activebackground=COL_BTN_DEFAULT,
            activeforeground=COL_TEXT,
            font=FONT_BUTTON,     # centralized
            relief="flat"
        )
        self.button.pack(fill="both", expand=True)

        if self.latch_mode.get() and self.latched:
            self.button.config(bg=COL_BTN_LATCHED, activebackground=COL_BTN_LATCHED)
        self.name.trace_add("write", lambda *_: self.button.config(text=self.name.get()))

        self.button.bind("<Button-1>", self.on_press)
        self.button.bind("<ButtonRelease-1>", self.on_release)
        self.button.bind("<Button-3>", self.show_context_menu)
        self.bind("<Button-3>", self.show_context_menu)
    
    def set_from_midi(self, value: int):
        """Update button UI/state from incoming MIDI *without* sending MIDI back."""
        v = int(value)
        if self.latch_mode.get():
            # Latch follows value >= 64
            self.latched = (v >= 64)
            self.button.config(
                bg=COL_BTN_LATCHED if self.latched else COL_BTN_DEFAULT,
                activebackground=COL_BTN_LATCHED if self.latched else COL_BTN_DEFAULT
            )
        else:
            # Momentary: >0 = down, 0 = up
            if v > 0:
                self.button.config(relief="sunken")   # fixed stray paren
            else:
                self.button.config(relief="flat")

    def on_press(self, event):
        if self.latch_mode.get():
            self.latched = not self.latched
            val = self.value_on if self.latched else self.value_off
            self.send_midi(val)
            self.button.config(
                bg=COL_BTN_LATCHED if self.latched else COL_BTN_DEFAULT,
                activebackground=COL_BTN_LATCHED if self.latched else COL_BTN_DEFAULT
            )
        else:
            self.send_midi(self.value_on)
            self.button.config(relief="sunken")

    def on_release(self, event):
        if not self.latch_mode.get():
            self.send_midi(self.value_off)
            self.button.config(relief="flat")

    def send_midi(self, val):
        send_midi(val, self.channel, self.control, self.mode)

    def show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0, bg=COL_FRAME, fg=COL_TEXT, activebackground=COL_ACCENT, font=FONT_UI)
        def open_setup():
            win = tk.Toplevel(self)
            win.title("Button Setup")
            win.configure(bg=COL_FRAME)
            win.geometry("290x200")

            tk.Label(win, text="Button Label", font=FONT_HEADER,
                     bg=COL_FRAME, fg=COL_TEXT).grid(row=0, column=0, padx=8, pady=6)
            tk.Entry(win, textvariable=self.name,
                     font=FONT_UI, bg=COL_BG, fg=COL_ACCENT,
                     insertbackground=COL_ACCENT, relief="flat").grid(row=0, column=1, padx=8, pady=6)

            tk.Label(win, text="Mode", font=FONT_HEADER,
                     bg=COL_FRAME, fg=COL_TEXT).grid(row=1, column=0, padx=8, pady=6)
            ttk.Combobox(win, textvariable=self.mode,
                         values=["CC", "Note", "Aftertouch"],
                         state="readonly", width=10).grid(row=1, column=1, padx=8, pady=6)

            tk.Label(win, text="Channel", font=FONT_HEADER,
                     bg=COL_FRAME, fg=COL_TEXT).grid(row=2, column=0, padx=8, pady=6)
            ttk.Combobox(win, textvariable=self.channel,
                         values=[str(i) for i in range(1, 17)],
                         state="readonly", width=4).grid(row=2, column=1, padx=8, pady=6)

            tk.Label(win, text="CC/Note", font=FONT_HEADER,
                     bg=COL_FRAME, fg=COL_TEXT).grid(row=3, column=0, padx=8, pady=6)
            ttk.Combobox(win, textvariable=self.control,
                         values=[str(i) for i in range(0, 128)],
                         state="readonly", width=5).grid(row=3, column=1, padx=8, pady=6)

            tk.Checkbutton(win, text="Latch Mode", variable=self.latch_mode,
                           bg=COL_FRAME, fg=COL_TEXT, selectcolor=COL_ACCENT,
                           activeforeground=COL_ACCENT, activebackground=COL_FRAME, font=FONT_UI).grid(
                row=4, column=0, columnspan=2, pady=(6, 4))

            tk.Button(win, text="Close", command=win.destroy,
                      bg=COL_ACCENT, fg=COL_TEXT, font=FONT_BUTTON,
                      relief="flat", width=12).grid(row=5, column=0, columnspan=2, pady=(10, 8))

        menu.add_command(label="MIDI Setup", command=open_setup)
        menu.add_command(label="Duplicate", command=lambda: duplicate(self))
        menu.add_command(label="Delete", command=lambda: self.master.destroy())
        menu.tk_popup(event.x_root, event.y_root)

    def get_state(self):
        if self.master:
            self.master.update_idletasks()
            info = self.master.place_info()
        else:
            info = {"x": 100, "y": 100, "width": 120, "height": 100}
        return {
            "name": self.name.get(),
            "mode": self.mode.get(),
            "channel": int(self.channel.get()),
            "control": int(self.control.get()),
            "latch": self.latch_mode.get(),
            "latched": self.latched,
            "x": int(info.get("x", 100)),
            "y": int(info.get("y", 100)),
            "width": int(info.get("width", 120)),
            "height": int(info.get("height", 100)),
        }

class MidiRadioGroupFrame(tk.Frame):
    def __init__(self, master, state=None):
        super().__init__(master, bg=COL_FRAME)

        # Model vars
        self.selected    = tk.IntVar(value=state["selected"] if state else 0)
        self.mode        = tk.StringVar(value=state["mode"] if state else "CC")
        self.channel     = tk.StringVar(value=str(state["channel"]) if state else "1")
        self.orientation = tk.StringVar(value=state.get("orientation", "vertical") if state else "vertical")

        # --- lowest-edge bucket helper (first bucket starts at 1, not 0) ---
        def bucket_low(i: int, n: int) -> int:
            n = max(1, int(n))
            v = (i * 128) // n
            return 1 if v <= 0 else min(127, v)

        # Normalize button_data from state or default
        if state and "buttons" in state:
            raw = state["buttons"]
            n = max(len(raw), 1)
            self.button_data = []
            for i, b in enumerate(raw):
                self.button_data.append({
                    "label": b.get("label", f"{i+1}"),
                    "control": int(b.get("control", 0)),
                    "value": int(b["value"]) if "value" in b else bucket_low(i, n),
                })
        else:
            n = 3
            self.button_data = [
                {"label": f"{i+1}", "control": 0, "value": bucket_low(i, n)}
                for i in range(n)
            ]

        self.control_map = {}   # idx -> (label, control, value)
        self.buttons = []
        self.container = None   # created in rebuild_controls()

        # Build initial UI
        self.rebuild_controls()

        # Track selection for visuals
        self.selected.trace_add("write", lambda *_: self.update_visuals())
        self.update_visuals()

    def rebuild_controls(self):
        """Destroy and recreate the radio button container + buttons from self.button_data,
        using a grid layout so all buttons always fit (no hidden last item)."""
        # Remove old container if present
        try:
            if getattr(self, "container", None) and self.container.winfo_exists():
                self.container.destroy()
        except Exception:
            pass

        self.control_map = {}
        self.buttons = []

        # Fresh container that follows the outer frame size
        self.container = tk.Frame(self, bg=COL_FRAME)
        self.container.pack(fill="both", expand=True, padx=RADIO_PAD, pady=RADIO_PAD)

        # Disable propagation so container honors DraggableResizableFrame size
        self.container.pack_propagate(False)
        self.container.grid_propagate(False)

        # Build buttons
        for idx, data in enumerate(self.button_data):
            label   = data.get("label", f"{idx+1}")
            control = int(data.get("control", 0))
            value   = int(data.get("value", 0))
            self.control_map[idx] = (label, control, value)

            rb = tk.Radiobutton(
                self.container,
                text=label,
                variable=self.selected,
                value=idx,
                command=self.send_midi,
                indicatoron=0,
                font=BUTTON_FONT,   # named font (FONT_RADIO)
                bg=COL_BTN,
                fg=BUTTON_FG,
                selectcolor=COL_BTN_LATCHED,
                activebackground=COL_BTN_LATCHED,
                activeforeground=BUTTON_FG,
                relief="flat",
                bd=2,
            )
            self.buttons.append(rb)

        # Lay out with grid so all buttons always stay visible
        if self.orientation.get() == "horizontal":
            cols = len(self.buttons)
            for c in range(cols):
                self.container.grid_columnconfigure(c, weight=1, uniform="rb")
            self.container.grid_rowconfigure(0, weight=1, uniform="rb")
            for c, rb in enumerate(self.buttons):
                rb.grid(row=0, column=c, padx=RADIO_PAD, pady=RADIO_PAD, sticky="nsew")
        else:
            rows = len(self.buttons)
            for r in range(rows):
                self.container.grid_rowconfigure(r, weight=1, uniform="rb")
            self.container.grid_columnconfigure(0, weight=1, uniform="rb")
            for r, rb in enumerate(self.buttons):
                rb.grid(row=r, column=0, padx=RADIO_PAD, pady=RADIO_PAD, sticky="nsew")

        # Context menu binding (actual menu in Part 2)
        self.bind("<Button-3>", self.show_context_menu)
        for rb in self.buttons:
            rb.bind("<Button-3>", self.show_context_menu)

        self.update_idletasks()
        # Ensure grid doesn’t collapse to 0x0 in weird edge cases
        try:
            self.container.minsize(1, 1)
        except Exception:
            pass
        self.update_visuals()

    def update_visuals(self):
        sel = self.selected.get()
        for idx, rb in enumerate(self.buttons):
            is_sel = (idx == sel)
            rb.config(
                bg=COL_BTN_LATCHED if is_sel else COL_BTN,
                activebackground=COL_BTN_LATCHED if is_sel else COL_BTN
            )

    def _index_for_cc(self, control_num: int, value: int):
        candidates = [(idx, int(val)) for idx, (_lbl, ctrl, val) in self.control_map.items() if ctrl == int(control_num)]
        if not candidates:
            return None
        value = max(0, min(127, int(value)))
        return min(candidates, key=lambda p: abs(p[1] - value))[0]

    def _index_for_note(self, note_num: int, velocity: int):
        candidates = [(idx, int(val)) for idx, (_lbl, note, val) in self.control_map.items() if note == int(note_num)]
        if not candidates:
            return None
        velocity = max(0, min(127, int(velocity)))
        return min(candidates, key=lambda p: abs(p[1] - velocity))[0]

    def set_from_midi_cc(self, control_num: int, value: int):
        idx = self._index_for_cc(control_num, value)
        if idx is not None and idx != self.selected.get():
            self.select_index_external(idx)

    def set_from_midi_note(self, note_num: int, velocity: int):
        idx = self._index_for_note(note_num, velocity)
        if idx is not None and idx != self.selected.get():
            self.select_index_external(idx)

    def select_index_external(self, idx: int):
        self.selected.set(idx)
        self.update_visuals()

    def send_midi(self):
        try:
            idx = self.selected.get()
            _, control, send_val = self.control_map[idx]
            value = max(0, min(127, int(send_val)))
            mode = self.mode.get()
            ch = int(self.channel.get()) - 1

            if mode == "CC":
                msg = Message("control_change", channel=ch, control=control, value=value)
            elif mode == "Note":
                msg = Message("note_on", channel=ch, note=control, velocity=value)
            elif mode == "Aftertouch":
                msg = Message("aftertouch", channel=ch, value=value)
            else:
                return

            midi_out.send(msg)
            print("Sent:", msg)
        except Exception as e:
            print("Radio MIDI send error:", e)

    def show_context_menu(self, event):
        # Implemented in Part 2 (avoid NameError if only Part 1 runs)
        try:
            menu = tk.Menu(self, tearoff=0, bg=COL_FRAME, fg=COL_TEXT, activebackground=COL_ACCENT, font=FONT_UI)
            menu.add_command(label="Edit Group Setup", command=lambda: open_radio_group_setup(self))
            menu.add_command(label="Duplicate", command=lambda: duplicate(self))
            menu.add_command(label="Delete", command=lambda: self.master.destroy())
            menu.tk_popup(event.x_root, event.y_root)
        except Exception:
            pass

    def get_state(self):
        if self.master:
            self.master.update_idletasks()
            info = self.master.place_info()
        else:
            info = {"x": 100, "y": 100, "width": 200, "height": 200}
        return {
            "type": "radio",
            "mode": self.mode.get(),
            "channel": int(self.channel.get()),
            "selected": self.selected.get(),
            "buttons": self.button_data,
            "orientation": self.orientation.get(),
            "x": int(info.get("x", 100)),
            "y": int(info.get("y", 100)),
            "width": int(info.get("width", 200)),
            "height": int(info.get("height", 200)),
        }
    


















# ==== PART 2/2 — from show_background_menu() to end ====

import time  # for lightweight motion throttling

# --- Guard to prevent MIDI echo/feedback when reflecting incoming MIDI to UI ---
UPDATING_FROM_MIDI = False

# --- Grouping support ---
group_boxes = []  # holds GroupBoxFrame instances

# ---- Scrollregion coalescing & suppression (ANTI-JITTER) ----
SR_SCHEDULED = False
SUPPRESS_SCROLL_UPDATES = False
# We temporarily unbind <Configure> on these to stop layout thrash during group moves
_CFG_BOUND = {"scrollable": True, "canvas": True}

def schedule_scroll_update():
    """Queue a single scrollregion update for the next idle moment."""
    global SR_SCHEDULED
    if SR_SCHEDULED or SUPPRESS_SCROLL_UPDATES:
        return
    SR_SCHEDULED = True
    root.after_idle(_perform_scroll_update)

def _perform_scroll_update():
    global SR_SCHEDULED
    SR_SCHEDULED = False
    if SUPPRESS_SCROLL_UPDATES:
        return
    update_scroll_region()  # defined in Part 1

def _begin_suppression():
    """Stop churn from <Configure> while we drag/resize groups."""
    global SUPPRESS_SCROLL_UPDATES, _CFG_BOUND
    SUPPRESS_SCROLL_UPDATES = True
    # Temporarily disable handlers that cause reflow
    if _CFG_BOUND["scrollable"]:
        try:
            scrollable_frame.unbind("<Configure>")
        except Exception:
            pass
        _CFG_BOUND["scrollable"] = False
    if _CFG_BOUND["canvas"]:
        try:
            canvas.unbind("<Configure>")
        except Exception:
            pass
        _CFG_BOUND["canvas"] = False

def _end_suppression():
    """Re-enable handlers and do exactly one scroll update."""
    global SUPPRESS_SCROLL_UPDATES, _CFG_BOUND
    SUPPRESS_SCROLL_UPDATES = False
    # Rebind the handlers we disabled
    try:
        canvas.bind("<Configure>", _on_canvas_configure)
    except Exception:
        pass
    try:
        scrollable_frame.bind("<Configure>", _on_frame_configure)
    except Exception:
        pass
    _CFG_BOUND["scrollable"] = True
    _CFG_BOUND["canvas"] = True
    schedule_scroll_update()


# ---------------- Background (canvas) context menu ----------------
def show_background_menu(event):
    menu = tk.Menu(root, tearoff=0, bg=COL_FRAME, fg=COL_TEXT, activebackground=COL_ACCENT)
    menu.add_command(label="Add Slider", command=add_slider)
    menu.add_command(label="Add Button", command=add_midi_button)
    menu.add_command(label="Add Radio Group", command=add_radio_group)
    menu.add_command(label="Add Group Box", command=add_group_box)
    menu.add_separator()
    menu.add_command(label="Save Setup", command=save_state)
    menu.add_command(label="Load Setup", command=load_state)

    def _toggle_lock():
        toggle_lock()
    menu.add_separator()
    lock_label = "Unlock Controls" if locked.get() else "Lock Controls"
    menu.add_command(label=lock_label, command=_toggle_lock)

    if output_names:
        menu.add_separator()
        menu.add_command(label="Output Port")
        for port in output_names:
            menu.add_radiobutton(label=f"→ {port}", variable=selected_port, value=port, command=select_port)

    if input_names:
        menu.add_separator()
        menu.add_command(label="Input Port")
        for port in input_names:
            menu.add_radiobutton(label=f"← {port}", variable=selected_input_port, value=port, command=listen_midi_input)

    menu.tk_popup(event.x_root, event.y_root)


# ---------------- Adders / Duplicator ----------------
def add_radio_group(state=None):
    frame = DraggableResizableFrame(scrollable_frame, bg=COL_FRAME, bd=2, relief="ridge")

    if state:
        x, y = state.get("x", 100), state.get("y", 100)
        w, h = state.get("width", 220), state.get("height", 200)
    else:
        x, y, w, h = get_spawn_geometry(radio_groups, 200)

    frame.place(x=x, y=y, width=w, height=h)

    radio_group = MidiRadioGroupFrame(frame, state)
    radio_group.pack(fill="both", expand=True, padx=4, pady=4)

    for wdg in (frame, radio_group):
        wdg.bind("<Button-3>", lambda e, rg=radio_group: rg.show_context_menu(e))

    radio_groups.append({"frame": frame, "group": radio_group})
    schedule_scroll_update()


def add_slider(state=None):
    frame = DraggableResizableFrame(scrollable_frame, bg=COL_FRAME, bd=2, relief="ridge")

    if state:
        x, y = state.get("x", 10), state.get("y", 10)
        w, h = state.get("width", DEFAULT_WIDTH), state.get("height", DEFAULT_HEIGHT_SLIDER)
    else:
        x, y, w, h = get_spawn_geometry(sliders, DEFAULT_HEIGHT_SLIDER)

    frame.place(x=x, y=y, width=w, height=h)

    container = tk.Frame(frame, bg=COL_FRAME)
    container.pack(fill="both", expand=True, padx=4, pady=4)
    container.pack_propagate(False)

    container.grid_rowconfigure(0, weight=0)  # name
    container.grid_rowconfigure(1, weight=0)  # value
    container.grid_rowconfigure(2, weight=1)  # slider stretches
    container.grid_columnconfigure(0, weight=1)

    mode_var    = tk.StringVar(value=state["mode"]    if state and "mode" in state else "CC")
    channel_var = tk.StringVar(value=str(state["channel"]) if state and "channel" in state else "1")
    control_var = tk.StringVar(value=str(state["control"]) if state and "control" in state else "1")
    name_var    = tk.StringVar(value=state.get("name", "Slider") if state else "Slider")

    name_entry = tk.Entry(container, textvariable=name_var, font=FONT_HEADER,
                          bg=COL_FRAME, fg=COL_SLIDER_NAME, insertbackground=COL_SLIDER_NAME,
                          relief="flat", highlightthickness=0, justify="center")
    name_entry.grid(row=0, column=0, sticky="we")

    value_var = tk.StringVar(value=str(state.get("value", 0) if state else 0))
    value_label = tk.Label(container, textvariable=value_var,
                           font=FONT_VALUE, bg=COL_FRAME, fg=COL_SLIDER_VALUE)
    value_label.grid(row=1, column=0, sticky="we")

    val_slider = tk.Scale(
        container, from_=127, to=0, orient=tk.VERTICAL,
        sliderlength=32,
        font=FONT_UI,
        troughcolor=COL_BG, fg=COL_ACCENT, bg=COL_FRAME,
        highlightthickness=0, bd=0, activebackground=COL_ACCENT,
        showvalue=0
    )
    val_slider.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)

    if state and "value" in state:
        val_slider.set(state["value"])

    def update_val(val, ch=channel_var, ctrl=control_var, mode=mode_var):
        value_var.set(val)
        if UPDATING_FROM_MIDI:
            return
        send_midi(val, ch, ctrl, mode)

    val_slider.config(command=update_val)

    slider_entry = {
        "frame": frame,
        "container": container,
        "slider": val_slider,
        "mode": mode_var,
        "channel": channel_var,
        "control": control_var,
        "name": name_var,
        "name_entry": name_entry,
    }
    val_slider._slider_entry_ref = slider_entry
    sliders.append(slider_entry)

    for wdg in (frame, container, name_entry, value_label, val_slider):
        wdg.bind("<Button-3>", lambda e, s=slider_entry: show_context_menu(e, s))

    resize_slider(slider_entry)
    root.after_idle(lambda: resize_slider(slider_entry))

    schedule_scroll_update()
    return slider_entry


def add_midi_button(state=None):
    frame = DraggableResizableFrame(scrollable_frame, bg=COL_FRAME, bd=2, relief="ridge")
    if state:
        x = state.get("x", 100)
        y = state.get("y", 100)
        w = state.get("width", DEFAULT_WIDTH)
        h = state.get("height", DEFAULT_HEIGHT_BUTTON)
    else:
        x, y, w, h = get_spawn_geometry(buttons, DEFAULT_HEIGHT_BUTTON)

    frame.place(x=x, y=y, width=w, height=h)

    button = MidiButtonFrame(frame, state)
    button.pack(fill="both", expand=True, padx=4, pady=4)

    buttons.append(button)

    frame.bind("<Button-3>", lambda e, b=button: b.show_context_menu(e))
    schedule_scroll_update()


def duplicate(widget):
    if not hasattr(widget, "get_state"):
        print("Cannot duplicate: missing get_state()")
        return

    state = widget.get_state()

    if isinstance(widget, MidiButtonFrame):
        x, y, _, _ = get_spawn_geometry(buttons, DEFAULT_HEIGHT_BUTTON)
        state["x"] = x
        state["y"] = y
        add_midi_button(state)

    elif isinstance(widget, MidiRadioGroupFrame):
        x, y, _, _ = get_spawn_geometry([], 200)
        state["x"] = x
        state["y"] = y
        add_radio_group(state)

    else:
        x, y, _, _ = get_spawn_geometry(sliders, DEFAULT_HEIGHT_SLIDER)
        state["x"], state["y"] = x, y
        add_slider(state)
        resize_slider(sliders[-1])


# ---------------- Draggable/Resizable container ----------------
class DraggableResizableFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        DRF_INSTANCES.append(self)

        self._drag_data = {"x": 0, "y": 0}
        self._resize_data = {"active": False, "corner": None, "x": 0, "y": 0, "w": 0, "h": 0, "absx": 0, "absy": 0}

        self.grips = {
            "nw": tk.Label(self, bg=COL_ACCENT, width=1, height=1, cursor="top_left_corner"),
            "ne": tk.Label(self, bg=COL_ACCENT, width=1, height=1, cursor="top_right_corner"),
            "se": tk.Label(self, bg=COL_ACCENT, width=1, height=1, cursor="bottom_right_corner"),
            "sw": tk.Label(self, bg=COL_ACCENT, width=1, height=1, cursor="bottom_left_corner"),
        }
        for corner in ("nw", "ne", "se", "sw"):
            self.grips[corner].bind("<ButtonPress-1>", lambda e, c=corner: self.start_resize(e, c))
            self.grips[corner].bind("<B1-Motion>", self.do_resize)
            self.grips[corner].bind("<ButtonRelease-1>", self.stop_resize)

        self.update_grips()

        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)
        self.bind("<ButtonRelease-1>", self.snap_to_grid)

    def destroy(self):
        try:
            if self in DRF_INSTANCES:
                DRF_INSTANCES.remove(self)
        except Exception:
            pass
        super().destroy()

    def update_grips(self):
        for g in list(self.grips.values()):
            try:
                if g.winfo_exists():
                    g.place_forget()
            except Exception:
                pass

        if not locked.get():
            size = 10
            try:
                if self.grips["nw"].winfo_exists():
                    self.grips["nw"].place(relx=0.0, rely=0.0, anchor="nw", width=size, height=size)
                if self.grips["ne"].winfo_exists():
                    self.grips["ne"].place(relx=1.0, rely=0.0, anchor="ne", width=size, height=size)
                if self.grips["se"].winfo_exists():
                    self.grips["se"].place(relx=1.0, rely=1.0, anchor="se", width=size, height=size)
                if self.grips["sw"].winfo_exists():
                    self.grips["sw"].place(relx=0.0, rely=1.0, anchor="sw", width=size, height=size)
                for g in self.grips.values():
                    try:
                        if g.winfo_exists():
                            g.lift()
                    except Exception:
                        pass
            except Exception:
                pass

    def start_drag(self, event):
        if locked.get() or self._resize_data["active"]:
            return
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def do_drag(self, event):
        if locked.get() or self._resize_data["active"]:
            return
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.winfo_x() + dx
        y = self.winfo_y() + dy
        self.place(x=x, y=y)
        schedule_scroll_update()

    def snap_to_grid(self, event):
        if self._resize_data["active"]:
            return
        x = round(self.winfo_x() / GRID_SIZE) * GRID_SIZE
        y = round(self.winfo_y() / GRID_SIZE) * GRID_SIZE
        self.place(x=x, y=y)
        schedule_scroll_update()

    def start_resize(self, event, corner):
        if locked.get():
            return
        _begin_suppression()  # smoother while any DRF is resizing
        self._resize_data.update({
            "active": True, "corner": corner, "x": event.x_root, "y": event.y_root,
            "w": self.winfo_width(), "h": self.winfo_height(),
            "absx": self.winfo_x(), "absy": self.winfo_y(),
        })

    def do_resize(self, event):
        rd = self._resize_data
        if not rd["active"]:
            return
        dx = event.x_root - rd["x"]
        dy = event.y_root - rd["y"]

        new_x, new_y = rd["absx"], rd["absy"]
        new_w, new_h = rd["w"], rd["h"]

        c = rd["corner"]
        if c == "se":
            new_w = rd["w"] + dx; new_h = rd["h"] + dy
        elif c == "ne":
            new_w = rd["w"] + dx; new_h = rd["h"] - dy; new_y = rd["absy"] + dy
        elif c == "sw":
            new_w = rd["w"] - dx; new_h = rd["h"] + dy; new_x = rd["absx"] + dx
        elif c == "nw":
            new_w = rd["w"] - dx; new_h = rd["h"] - dy; new_x = rd["absx"] + dx; new_y = rd["absy"] + dy

        new_w = max(MIN_WIDTH, round(new_w / GRID_SIZE) * GRID_SIZE)
        new_h = max(MIN_HEIGHT, round(new_h / GRID_SIZE) * GRID_SIZE)
        new_x = round(new_x / GRID_SIZE) * GRID_SIZE
        new_y = round(new_y / GRID_SIZE) * GRID_SIZE

        self.place(x=new_x, y=new_y, width=new_w, height=new_h)
        schedule_scroll_update()

        for widget in self.winfo_children():
            if isinstance(widget, tk.Frame):
                for sub in widget.winfo_children():
                    if isinstance(sub, tk.Scale) and hasattr(sub, "_slider_entry_ref"):
                        resize_slider(sub._slider_entry_ref)

    def stop_resize(self, event):
        self._resize_data["active"] = False
        _end_suppression()
        schedule_scroll_update()


# ---------------- Group Box ----------------
def _drf_bbox(drf):
    drf.update_idletasks()
    x, y = drf.winfo_x(), drf.winfo_y()
    return x, y, x + drf.winfo_width(), y + drf.winfo_height()

def _rect_contains_point(rect, px, py):
    x1, y1, x2, y2 = rect
    return (x1 <= px <= x2) and (y1 <= py <= y2)

def _identify_widget_for_drf(drf):
    if getattr(drf, "is_group_box", False):
        return ("group", drf)
    for ch in drf.winfo_children():
        if isinstance(ch, tk.Frame):
            for sub in ch.winfo_children():
                if isinstance(sub, tk.Scale) and hasattr(sub, "_slider_entry_ref"):
                    return ("slider", sub._slider_entry_ref)
    for ch in drf.winfo_children():
        if isinstance(ch, MidiButtonFrame):
            return ("button", ch)
    for ch in drf.winfo_children():
        if isinstance(ch, MidiRadioGroupFrame):
            return ("radio", ch)
    return (None, None)

def _iter_member_frames():
    for child in scrollable_frame.winfo_children():
        if isinstance(child, DraggableResizableFrame) and not getattr(child, "is_group_box", False):
            yield child

def remove_button(button_frame):
    try:
        buttons.remove(button_frame)
    except ValueError:
        pass
    try:
        button_frame.master.destroy()
    except Exception:
        pass

def remove_radio_group_by_group(group_widget):
    target = None
    for rg in radio_groups:
        if rg["group"] is group_widget:
            target = rg
            break
    if target:
        try:
            radio_groups.remove(target)
        except ValueError:
            pass
        try:
            target["frame"].destroy()
        except Exception:
            pass


class GroupBoxFrame(DraggableResizableFrame):
    """A lasso-like box that groups widgets whose centers lie inside it.
       Always kept under other controls."""
    def __init__(self, parent, title="Group", **kwargs):
        super().__init__(parent, **kwargs)
        self.is_group_box = True
        self.title = tk.StringVar(value=title)
        self.members = []
        self._last_motion_ts = 0.0  # throttle group motion to ~100 fps

        self._cnv = tk.Canvas(self, bg=COL_BG, highlightthickness=0, bd=0)
        self._cnv.pack(fill="both", expand=True)

        self._title = tk.Label(self, textvariable=self.title,
                               bg=COL_BG, fg=COL_ACCENT, font=FONT_LABEL)
        self._title.place(x=6, y=4)

        for src in (self, self._cnv, self._title):
            src.bind("<Button-1>", self._on_press)
            src.bind("<B1-Motion>", self.do_drag)
            src.bind("<ButtonRelease-1>", self.snap_to_grid)
            src.bind("<Button-3>", self._show_menu)

        self.bind("<Configure>", lambda e: self._redraw())

        self.compute_members()
        self._redraw()

    def _redraw(self):
        self._cnv.delete("all")
        w = max(1, self.winfo_width() - 1)
        h = max(1, self.winfo_height() - 1)
        self._cnv.create_rectangle(1, 1, w, h, outline=COL_ACCENT, width=2, dash=(5, 4))
        try: self._title.lift()
        except Exception: pass

    def update_grips(self):
        super().update_grips()
        try: self.lower()
        except Exception: pass

    def compute_members(self):
        gx1, gy1, gx2, gy2 = _drf_bbox(self)
        self.members = []
        for drf in _iter_member_frames():
            x1, y1, x2, y2 = _drf_bbox(drf)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            if _rect_contains_point((gx1, gy1, gx2, gy2), cx, cy):
                self.members.append(drf)

    def _on_press(self, event):
        if locked.get() or self._resize_data["active"]:
            return
        _begin_suppression()  # big win for groups
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self._start_pos = (self.winfo_x(), self.winfo_y())
        self._member_starts = {m: (m.winfo_x(), m.winfo_y()) for m in self.members}
        self._last_motion_ts = 0.0

    def do_drag(self, event):
        if locked.get() or self._resize_data["active"]:
            return
        # Throttle to avoid overwhelming Tk with hundreds of .place calls per second
        now = time.time()
        if (now - self._last_motion_ts) < 0.01:  # ~100 fps cap
            return
        self._last_motion_ts = now

        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        new_x = self.winfo_x() + dx
        new_y = self.winfo_y() + dy
        self.place(x=new_x, y=new_y)

        off_x = new_x - self._start_pos[0]
        off_y = new_y - self._start_pos[1]
        for m, (mx, my) in self._member_starts.items():
            m.place(x=mx + off_x, y=my + off_y)

        # No scroll update during suppression; one will run at the end
        # (we still allow coalesced updates if suppression was lifted)
        # schedule_scroll_update()  # intentionally omitted here

    def snap_to_grid(self, event):
        if getattr(self, "_resize_data", {}).get("active"):
            return
        gx = round(self.winfo_x() / GRID_SIZE) * GRID_SIZE
        gy = round(self.winfo_y() / GRID_SIZE) * GRID_SIZE
        dx = gx - self.winfo_x()
        dy = gy - self.winfo_y()
        self.place(x=gx, y=gy)
        for m in self.members:
            m.place(x=m.winfo_x() + dx, y=m.winfo_y() + dy)
        _end_suppression()

    def stop_resize(self, event):
        super().stop_resize(event)
        self.compute_members()
        self._redraw()
        _end_suppression()

    # --- Context menu (only the two items you want) ---
    def _show_menu(self, event):
        menu = tk.Menu(self, tearoff=0, bg=COL_FRAME, fg=COL_TEXT, activebackground=COL_ACCENT, font=FONT_UI)
        menu.add_command(label="Rename Group", command=self._rename)
        menu.add_command(label="Recompute Members", command=self.compute_members)
        menu.add_separator()
        menu.add_command(label="Duplicate Box + Members", command=self.duplicate_group_box)
        menu.add_separator()
        menu.add_command(label="Delete Groupbox and Contents", command=self.delete_group_and_contents)
        menu.tk_popup(event.x_root, event.y_root)

    def _rename(self):
        top = tk.Toplevel(self)
        top.title("Group Name")
        top.configure(bg=COL_FRAME)
        tk.Label(top, text="Title", bg=COL_FRAME, fg=COL_TEXT, font=FONT_LABEL).grid(row=0, column=0, padx=8, pady=8)
        e = tk.Entry(top, textvariable=self.title, bg=COL_BG, fg=COL_ACCENT, insertbackground=COL_ACCENT, relief="flat")
        e.grid(row=0, column=1, padx=8, pady=8)
        tk.Button(top, text="Close", command=top.destroy,
                  bg=COL_ACCENT, fg=COL_TEXT, font=FONT_BUTTON, relief="flat").grid(row=1, column=0, columnspan=2, pady=8)

    def delete_group_and_contents(self):
        """Delete this group box and every widget currently in it."""
        # Refresh membership, then remove each member cleanly
        self.compute_members()
        for m in list(self.members):
            wtype, payload = _identify_widget_for_drf(m)
            if wtype == "slider":
                remove_slider(payload)
            elif wtype == "button":
                remove_button(payload)
            elif wtype == "radio":
                remove_radio_group_by_group(payload)
        # Remove the group box itself
        try:
            group_boxes.remove(self)
        except ValueError:
            pass
        self.destroy()
        schedule_scroll_update()

    def duplicate_group_box(self, offset_px=20):
        """Duplicate this box and all its members to the RIGHT by 20px, vertically centered."""
        self.update_idletasks()
        x1, y1, x2, y2 = _drf_bbox(self)
        w, h = self.winfo_width(), self.winfo_height()
        cy = (y1 + y2) // 2
        new_x = x2 + offset_px
        new_y = cy - h // 2

        st = {"type": "group_box", "title": self.title.get(),
              "x": new_x, "y": new_y, "width": w, "height": h}

        new_gb = add_group_box(st)  # always lowered

        dx = new_x - self.winfo_x()
        dy = new_y - self.winfo_y()

        # Duplicate members into the new box's area
        self.compute_members()
        for m in list(self.members):
            wtype, payload = _identify_widget_for_drf(m)
            if wtype == "slider":
                ms = slider_state(payload)
                ms["x"], ms["y"] = m.winfo_x() + dx, m.winfo_y() + dy
                add_slider(ms)
            elif wtype == "button":
                ms = payload.get_state()
                ms["x"], ms["y"] = m.winfo_x() + dx, m.winfo_y() + dy
                add_midi_button(ms)
            elif wtype == "radio":
                ms = payload.get_state()
                ms["x"], ms["y"] = m.winfo_x() + dx, m.winfo_y() + dy
                add_radio_group(ms)

        new_gb.compute_members()
        schedule_scroll_update()

    def get_state(self):
        self.update_idletasks()
        info = self.place_info()
        def _ival(key, default):
            try: return int(info.get(key, default))
            except Exception: return default
        return {
            "type": "group_box",
            "title": self.title.get(),
            "x": _ival("x", 60),
            "y": _ival("y", 60),
            "width": _ival("width", 320),
            "height": _ival("height", 240),
        }


def add_group_box(state=None):
    """Create a group box; always lowered behind other controls."""
    if state:
        x, y = state.get("x", 60), state.get("y", 60)
        w, h = state.get("width", 320), state.get("height", 240)
        title = state.get("title", "Group")
    else:
        x, y, w, h = get_spawn_geometry([], 240)
        w = max(240, w + 180)
        title = "Group"

    gb = GroupBoxFrame(scrollable_frame, title=title, bg=COL_BG, bd=0, highlightthickness=0)
    gb.place(x=x, y=y, width=w, height=h)
    group_boxes.append(gb)
    gb.compute_members()
    gb._redraw()

    try: gb.lower()
    except Exception: pass

    gb.update_grips()
    schedule_scroll_update()
    return gb


# ---------------- Slider helpers ----------------
def resize_slider(slider_entry):
    container   = slider_entry["container"]
    slider      = slider_entry["slider"]
    name_entry  = slider_entry["name_entry"]

    container.update_idletasks()

    name_h = name_entry.winfo_reqheight()
    value_label = None
    for w in container.grid_slaves(row=1, column=0):
        value_label = w
        break
    value_h = value_label.winfo_reqheight() if value_label else 0

    reserved = name_h + value_h
    height   = container.winfo_height()
    width    = container.winfo_width()

    slider_length = max(20, height - reserved)
    slider.config(length=slider_length, width=max(30, int(width)))

    fr = slider_entry["frame"]
    if hasattr(fr, "grips"):
        for g in fr.grips.values():
            try:
                if g.winfo_exists():
                    g.lift()
            except Exception:
                pass


def slider_state(slider_entry):
    frame = slider_entry["frame"]
    frame.update_idletasks()
    info = frame.place_info()
    return {
        "value": slider_entry["slider"].get(),
        "mode": slider_entry["mode"].get(),
        "channel": int(slider_entry["channel"].get()),
        "control": int(slider_entry["control"].get()),
        "name": slider_entry["name"].get(),
        "x": int(info.get("x", 100)),
        "y": int(info.get("y", 100)),
        "width": int(info.get("width", MIN_WIDTH)),
        "height": int(info.get("height", MIN_HEIGHT)),
    }


def remove_slider(slider_entry):
    try:
        sliders.remove(slider_entry)
    except ValueError:
        pass
    try:
        slider_entry["frame"].destroy()
    except Exception:
        pass


# ---------------- MIDI ----------------
def open_midi_setup(slider_entry):
    win = tk.Toplevel(root)
    win.title("Slider Midi Settings ")
    win.configure(bg=COL_FRAME)
    win.geometry("200x150")

    tk.Label(win, text="Mode", font=FONT_HEADER, bg=COL_FRAME, fg=COL_TEXT).grid(row=0, column=0, sticky="e", padx=8, pady=6)
    ttk.Combobox(win, textvariable=slider_entry["mode"],
                 values=["CC", "Note", "Pitch Bend", "Aftertouch"],
                 state="readonly", width=10).grid(row=0, column=1, sticky="w", padx=8, pady=6)

    tk.Label(win, text="Channel", font=FONT_HEADER, bg=COL_FRAME, fg=COL_TEXT).grid(row=1, column=0, sticky="e", padx=8, pady=6)
    ttk.Combobox(win, textvariable=slider_entry["channel"],
                 values=[str(i) for i in range(1, 17)],
                 state="readonly", width=4).grid(row=1, column=1, sticky="w", padx=8, pady=6)

    tk.Label(win, text="cc/note", font=FONT_HEADER, bg=COL_FRAME, fg=COL_TEXT).grid(row=2, column=0, sticky="e", padx=8, pady=6)
    ttk.Combobox(win, textvariable=slider_entry["control"],
                 values=[str(i) for i in range(0, 128)],
                 state="readonly", width=5).grid(row=2, column=1, sticky="w", padx=8, pady=6)

    tk.Button(win, text="Close", command=win.destroy,
              bg=COL_ACCENT, fg=COL_TEXT, font=FONT_BUTTON,
              relief="flat", width=12).grid(row=3, column=0, columnspan=2, pady=(10, 8))


def send_midi(value, channel_var, control_var, mode_var):
    global midi_out
    if midi_out is None:
        print("No MIDI output selected.")
        return
    try:
        value = int(float(value))
        channel = int(channel_var.get()) - 1
        control = int(control_var.get())
        mode = mode_var.get()

        if mode == "CC":
            msg = Message("control_change", channel=channel, control=control, value=value)
        elif mode == "Note":
            msg = Message("note_on", channel=channel, note=control, velocity=value)
        elif mode == "Pitch Bend":
            pitch_val = int((value / 127.0) * 16383) - 8192
            msg = Message("pitchwheel", channel=channel, pitch=pitch_val)
        elif mode == "Aftertouch":
            msg = Message("aftertouch", channel=channel, value=value)
        else:
            return

        midi_out.send(msg)
        print(f"Sent {mode} | Channel {channel+1} | Number {control} | Value {value}")
    except Exception as e:
        print("MIDI Error:", e)


def listen_midi_input():
    def midi_loop():
        try:
            with mido.open_input(selected_input_port.get()) as midi_in:
                print(f"Listening for MIDI input on: {selected_input_port.get()}")
                for msg in midi_in:
                    if msg.type not in ("control_change", "note_on", "note_off", "pitchwheel", "aftertouch"):
                        continue

                    global UPDATING_FROM_MIDI
                    UPDATING_FROM_MIDI = True
                    try:
                        # ---------- SLIDERS ----------
                        for entry in sliders:
                            mode = entry["mode"].get()
                            ch = int(entry["channel"].get()) - 1
                            ctrl = int(entry["control"].get())
                            if getattr(msg, "channel", ch) != ch:
                                continue
                            if msg.type == "control_change" and mode == "CC" and msg.control == ctrl:
                                entry["slider"].set(msg.value)
                            elif msg.type == "note_on" and mode == "Note" and msg.note == ctrl:
                                entry["slider"].set(msg.velocity)
                            elif msg.type == "note_off" and mode == "Note" and msg.note == ctrl:
                                entry["slider"].set(0)
                            elif msg.type == "pitchwheel" and mode == "Pitch Bend":
                                val = int(((msg.pitch + 8192) / 16383.0) * 127)
                                entry["slider"].set(val)
                            elif msg.type == "aftertouch" and mode == "Aftertouch":
                                entry["slider"].set(msg.value)

                        # ---------- BUTTONS ----------
                        for btn in buttons:
                            mode = btn.mode.get()
                            ch = int(btn.channel.get()) - 1
                            ctrl = int(btn.control.get())
                            if getattr(msg, "channel", ch) != ch:
                                continue
                            if msg.type == "control_change" and mode == "CC" and msg.control == ctrl:
                                btn.set_from_midi(msg.value)
                            elif msg.type == "note_on" and mode == "Note" and msg.note == ctrl:
                                btn.set_from_midi(msg.velocity)
                            elif msg.type == "note_off" and mode == "Note" and msg.note == ctrl:
                                btn.set_from_midi(0)
                            elif msg.type == "aftertouch" and mode == "Aftertouch":
                                btn.set_from_midi(msg.value)

                        # ---------- RADIO GROUPS ----------
                        for rg in radio_groups:
                            group = rg["group"]
                            mode = group.mode.get()
                            ch = int(group.channel.get()) - 1
                            if getattr(msg, "channel", ch) != ch:
                                continue

                            if mode == "CC" and msg.type == "control_change":
                                group.set_from_midi_cc(msg.control, msg.value)
                            elif mode == "Note":
                                if msg.type == "note_on":
                                    group.set_from_midi_note(msg.note, getattr(msg, "velocity", 0))
                            elif mode == "Aftertouch" and msg.type == "aftertouch":
                                group.set_from_midi_cc(0, msg.value)
                    finally:
                        UPDATING_FROM_MIDI = False
        except Exception as e:
            print("MIDI input error:", e)

    threading.Thread(target=midi_loop, daemon=True).start()


def select_port():
    global midi_out
    if midi_out:
        try:
            midi_out.close()
        except Exception:
            pass
    try:
        midi_out = mido.open_output(selected_port.get())
        print(f"Connected to: {selected_port.get()}")
    except Exception as e:
        print("Failed to open port:", e)


# ---------------- Slider context menu ----------------
def show_context_menu(event, slider_entry):
    menu = tk.Menu(root, tearoff=0, bg=COL_FRAME, fg=COL_TEXT, activebackground=COL_ACCENT)
    menu.add_command(label="MIDI Setup", command=lambda: open_midi_setup(slider_entry))
    menu.add_command(label="Rename", command=lambda: slider_entry["name_entry"].focus_set())
    menu.add_command(label="Duplicate", command=lambda: duplicate(SliderProxy(slider_entry)))
    menu.add_command(label="Delete", command=lambda: remove_slider(slider_entry))
    menu.tk_popup(event.x_root, event.y_root)


# ---------------- Save/Load ----------------
def save_state():
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if not file_path:
        return

    data = {"widgets": []}

    for entry in sliders:
        try:
            widget_data = slider_state(entry)
            widget_data["type"] = "slider"
            data["widgets"].append(widget_data)
        except Exception as e:
            print(f"Error saving slider: {e}")

    for button in buttons:
        try:
            widget_data = button.get_state()
            widget_data["type"] = "button"
            data["widgets"].append(widget_data)
        except Exception as e:
            print(f"Error saving button: {e}")

    for rg in radio_groups:
        try:
            widget_data = rg["group"].get_state()
            widget_data["type"] = "radio"
            data["widgets"].append(widget_data)
        except Exception as e:
            print(f"Error saving radio group: {e}")

    for gb in group_boxes:
        try:
            data["widgets"].append(gb.get_state())
        except Exception as e:
            print(f"Error saving group box: {e}")

    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        current_filename.set(file_path.split("/")[-1])
        root.title(f"MIDI Controller - {current_filename.get()}")
        print("Session saved:", file_path)
    except Exception as e:
        print(f"Final save error: {e}")


def load_state():
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if not file_path:
        return

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            print("Widgets in JSON:", data.get("widgets"))
            print("Widget count:", len(data.get("widgets", [])))
    except Exception as e:
        print("Failed to load:", e)
        return

    for entry in sliders[:]:
        remove_slider(entry)

    for button in buttons[:]:
        try:
            button.master.destroy()
        except Exception:
            pass
    buttons.clear()

    for rg in radio_groups[:]:
        try:
            rg["frame"].destroy()
        except Exception:
            pass
    radio_groups.clear()

    for gb in group_boxes[:]:
        try:
            gb.destroy()
        except Exception:
            pass
    group_boxes.clear()

    for widget in scrollable_frame.winfo_children():
        if isinstance(widget, DraggableResizableFrame):
            widget.destroy()

    for item in data.get("widgets", []):
        t = item.get("type")
        if t == "slider":
            add_slider(item)
        elif t == "button":
            add_midi_button(item)
        elif t == "radio":
            add_radio_group(item)

    for item in data.get("widgets", []):
        if item.get("type") == "group_box":
            add_group_box(item)

    for gb in group_boxes:
        gb.compute_members()

    current_filename.set(file_path.split("/")[-1])
    root.title(f"MIDI Controller - {current_filename.get()}")
    print("Session loaded:", file_path)

    schedule_scroll_update()
    canvas.xview_moveto(0)
    canvas.yview_moveto(0)


# --------------- App wiring ---------------
if selected_port.get():
    select_port()
if selected_input_port.get():
    listen_midi_input()

def clear_focus(event):
    if not isinstance(event.widget, tk.Entry):
        root.focus_set()

root.bind_all("<Button-1>", clear_focus, add="+")

# root.after(50, add_slider)
# root.after(100, load_state)

root.mainloop()
# ==== END PART 2/2 ====
