import tkinter as tk
from tkinter import ttk, filedialog
import mido
from mido import Message
import json
import threading

COL_BG = "#1e1e1e"
COL_FRAME = "#2e2e2e"
COL_ACCENT = "#bd6500"
COL_TEXT = "#686868"
COL_BTN_HOVER = "#444444"
COL_BTN = "#333333"
ICON_RESIZE = ""
ICON_DRAG = ""
ICON_FONT = ("Helvetica", 16)  # consistent font size for icons
COL_SLIDER_NAME = "#df4600"   # Colour for slider name entry
COL_SLIDER_VALUE = "#fc7100"  # Colour for value label
COL_BTN_DEFAULT = "#444444"   # grey when not latched
COL_BTN_LATCHED = "#ff8800"   # orange when latched
GRID_SIZE = 10
MIN_WIDTH = 50
MIN_HEIGHT = 20
BUTTON_FONT = ("Helvetica", 14, "bold")
BUTTON_FG = "#ffffff"


# Put near your other globals
SR_W = 0   # current scrollregion width
SR_H = 0   # current scrollregion height
PADDING = 200
GROW_CHUNK = 1200  # how much extra room to add when we hit the edge


root = tk.Tk()

# Track current filename in the title bar
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
    print("Locked:", locked.get())

DEFAULT_WIDTH = MIN_WIDTH
DEFAULT_HEIGHT_SLIDER = 500
DEFAULT_HEIGHT_BUTTON = MIN_WIDTH
WIDGET_WIDTH = 60
SPAWN_GAP = 2

# Larger touch-friendly scrollbars
SCROLLBAR_WIDTH = 30  # adjust to taste

# ---------------- Canvas + Scrollbars ----------------
canvas_container = tk.Frame(root, bg=COL_BG)
canvas_container.pack(fill="both", expand=True)

# Use grid to remove the scrollbar corner
canvas_container.grid_rowconfigure(0, weight=1)
canvas_container.grid_columnconfigure(0, weight=1)

# Main canvas
canvas = tk.Canvas(canvas_container, bg=COL_BG, highlightthickness=0)
canvas.grid(row=0, column=0, sticky="nsew")

# Vertical scrollbar (touch friendly size)
v_scroll = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview, width=30)
v_scroll.grid(row=0, column=1, sticky="ns")

# Horizontal scrollbar (touch friendly size)
h_scroll = tk.Scrollbar(canvas_container, orient="horizontal", command=canvas.xview, width=30)
h_scroll.grid(row=1, column=0, sticky="ew")

canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)


# Inner frame (one window only)
scrollable_frame = tk.Frame(canvas, bg=COL_BG)
window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

# --- Canvas resize handler ---
def _on_canvas_configure(e):
    # Keep the embedded frame at least as large as the viewport, but prefer content size
    vw, vh = max(e.width, 1), max(e.height, 1)
    w = max(SR_W, vw + 1)
    h = max(SR_H, vh)
    canvas.itemconfig(window_id, width=w, height=h)
    canvas.configure(scrollregion=(0, 0, w, h))

# Put near your other globals
SR_W = 0   # current scrollregion width
SR_H = 0   # current scrollregion height
PADDING = 200
GROW_CHUNK = 1200  # how much extra room to add when we hit the edge

def open_radio_group_setup(radio_group):
    win = tk.Toplevel(root)
    win.title("Edit MIDI Radio Group")
    win.configure(bg=COL_FRAME)
    win.geometry("450x500")

    num_var = tk.IntVar(value=len(radio_group.button_data))
    mode_var = radio_group.mode
    channel_var = radio_group.channel
    orientation_var = radio_group.orientation

    entries = []

    # Static Top Controls
    top_frame = tk.Frame(win, bg=COL_FRAME)
    top_frame.pack(fill="x", padx=8, pady=6)

    tk.Label(top_frame, text="Number of Buttons", bg=COL_FRAME, fg=COL_TEXT).grid(row=0, column=0, padx=4, pady=4)
    tk.Spinbox(top_frame, from_=1, to=64, textvariable=num_var, width=5, command=lambda: build_entries()).grid(row=0, column=1, padx=4, pady=4)

    tk.Label(top_frame, text="MIDI Mode", bg=COL_FRAME, fg=COL_TEXT).grid(row=1, column=0, padx=4, pady=4)
    ttk.Combobox(top_frame, textvariable=mode_var, values=["CC", "Note", "Aftertouch"],
                 state="readonly", width=10).grid(row=1, column=1, padx=4, pady=4)

    tk.Label(top_frame, text="Channel", bg=COL_FRAME, fg=COL_TEXT).grid(row=2, column=0, padx=4, pady=4)
    ttk.Combobox(top_frame, textvariable=channel_var, values=[str(i) for i in range(1, 17)],
                 state="readonly", width=5).grid(row=2, column=1, padx=4, pady=4)

    tk.Label(top_frame, text="Orientation", bg=COL_FRAME, fg=COL_TEXT).grid(row=3, column=0, padx=4, pady=4)
    ttk.Combobox(top_frame, textvariable=orientation_var,
                 values=["vertical", "horizontal"], state="readonly", width=10).grid(row=3, column=1, padx=4, pady=4)

    # Scrollable middle section
    canvas = tk.Canvas(win, bg=COL_FRAME, highlightthickness=0)
    scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg=COL_FRAME)

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def build_entries():
        for widget in scroll_frame.winfo_children():
            widget.destroy()
        entries.clear()

        for i in range(num_var.get()):
            label_var = tk.StringVar()
            cc_var = tk.StringVar()

            if i < len(radio_group.button_data):
                label_var.set(radio_group.button_data[i]["label"])
                cc_var.set(str(radio_group.button_data[i]["control"]))
            else:
                label_var.set(f"Option {i+1}")
                cc_var.set("0")

            tk.Label(scroll_frame, text=f"Label {i+1}", bg=COL_FRAME, fg=COL_TEXT).grid(row=i, column=0, padx=4, pady=4)
            tk.Entry(scroll_frame, textvariable=label_var, width=12, bg=COL_BG, fg=COL_ACCENT,
                     insertbackground=COL_ACCENT).grid(row=i, column=1, padx=4, pady=4)

            tk.Label(scroll_frame, text="CC/Note", bg=COL_FRAME, fg=COL_TEXT).grid(row=i, column=2, padx=4, pady=4)
            cc_menu = ttk.Combobox(scroll_frame, textvariable=cc_var,
                                   values=[str(i) for i in range(0, 128)],
                                   state="readonly", width=6)
            cc_menu.grid(row=i, column=3, padx=4, pady=4)

            entries.append((label_var, cc_var))

    def apply_changes():
        radio_group.button_data = [
            {"label": label.get(), "control": int(cc.get())}
            for label, cc in entries
        ]

        radio_group.orientation.set(orientation_var.get())

        for btn in radio_group.buttons:
            btn.destroy()
        radio_group.buttons.clear()
        radio_group.control_map.clear()

        # ✅ Clear old widgets in case container exists
        for child in radio_group.winfo_children():
            child.destroy()

        container = tk.Frame(radio_group, bg=COL_FRAME)
        container.pack(fill="both", expand=True, padx=4, pady=4)

        for idx, data in enumerate(radio_group.button_data):
            radio_group.control_map[idx] = (data["label"], data["control"])
            rb = tk.Radiobutton(
                container,
                text=data["label"],
                variable=radio_group.selected,
                value=idx,
                command=radio_group.send_midi,
                indicatoron=0,
                font=BUTTON_FONT,
                bg=COL_BTN,
                fg=BUTTON_FG,
                selectcolor=COL_BTN_LATCHED,
                activebackground=COL_BTN_LATCHED,
                activeforeground=BUTTON_FG,
                relief="flat",
                bd=2,
                width=10,
                pady=10
            )

            if orientation_var.get() == "horizontal":
                rb.pack(side="left", padx=4, pady=4, fill="y", expand=True)
            else:
                rb.pack(side="top", padx=4, pady=4, fill="x", expand=True)

            radio_group.buttons.append(rb)

        # ✅ Rebind right-click menu
        radio_group.bind("<Button-3>", lambda e: radio_group.show_context_menu(e))
        for btn in radio_group.buttons:
            btn.bind("<Button-3>", lambda e: radio_group.show_context_menu(e))

        win.destroy()

    build_entries()

    apply_btn = tk.Button(win, text="Apply", command=apply_changes,
                          bg=COL_ACCENT, fg=COL_TEXT, font=("Helvetica", 10, "bold"),
                          relief="flat", width=12)
    apply_btn.pack(pady=12)

def update_scroll_region():
    global SR_W, SR_H

    max_right = 0
    max_bottom = 0
    for child in scrollable_frame.winfo_children():
        if isinstance(child, DraggableResizableFrame):
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

# Right-click background menu on canvas/inner frame
def show_background_menu(event):
    menu = tk.Menu(root, tearoff=0, bg=COL_FRAME, fg=COL_TEXT, activebackground=COL_ACCENT)
    menu.add_command(label="Add Slider", command=add_slider)
    menu.add_command(label="Add Button", command=add_midi_button)
    menu.add_command(label="Add Radio Group", command=add_radio_group)
    menu.add_separator()
    menu.add_command(label="Save Setup", command=save_state)
    menu.add_command(label="Load Setup", command=load_state)

    def _toggle_lock():
        locked.set(not locked.get())

    menu.add_separator()
    lock_label = " Unlock Controls" if locked.get() else "Lock Controls"
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

canvas.bind("<Button-3>", show_background_menu)
scrollable_frame.bind("<Button-3>", show_background_menu)

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
            font=("Helvetica", 12, "bold"),
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
                self.button.config(relief="sunken")
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
        menu = tk.Menu(self, tearoff=0, bg=COL_FRAME, fg=COL_TEXT, activebackground=COL_ACCENT)
        def open_setup():
            win = tk.Toplevel(self)
            win.title("MIDI Button Setup")
            win.configure(bg=COL_FRAME)
            win.geometry("240x180")

            tk.Label(win, text="Button Label", font=("Helvetica", 10, "bold"),
                     bg=COL_FRAME, fg=COL_TEXT).grid(row=0, column=0, padx=8, pady=6)
            tk.Entry(win, textvariable=self.name,
                     font=("Helvetica", 10), bg=COL_BG, fg=COL_ACCENT,
                     insertbackground=COL_ACCENT, relief="flat").grid(row=0, column=1, padx=8, pady=6)

            tk.Label(win, text="Mode", font=("Helvetica", 10, "bold"),
                     bg=COL_FRAME, fg=COL_TEXT).grid(row=1, column=0, padx=8, pady=6)
            ttk.Combobox(win, textvariable=self.mode,
                         values=["CC", "Note", "Aftertouch"],
                         state="readonly", width=10).grid(row=1, column=1, padx=8, pady=6)

            tk.Label(win, text="Channel", font=("Helvetica", 10, "bold"),
                     bg=COL_FRAME, fg=COL_TEXT).grid(row=2, column=0, padx=8, pady=6)
            ttk.Combobox(win, textvariable=self.channel,
                         values=[str(i) for i in range(1, 17)],
                         state="readonly", width=4).grid(row=2, column=1, padx=8, pady=6)

            tk.Label(win, text="CC/Note", font=("Helvetica", 10, "bold"),
                     bg=COL_FRAME, fg=COL_TEXT).grid(row=3, column=0, padx=8, pady=6)
            ttk.Combobox(win, textvariable=self.control,
                         values=[str(i) for i in range(0, 128)],
                         state="readonly", width=5).grid(row=3, column=1, padx=8, pady=6)

            tk.Checkbutton(win, text="Latch Mode", variable=self.latch_mode,
                           bg=COL_FRAME, fg=COL_TEXT, selectcolor=COL_ACCENT,
                           activeforeground=COL_ACCENT, activebackground=COL_FRAME).grid(
                row=4, column=0, columnspan=2, pady=(6, 4))

            tk.Button(win, text="Close", command=win.destroy,
                      bg=COL_ACCENT, fg=COL_TEXT, font=("Helvetica", 10, "bold"),
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

        self.selected = tk.IntVar(value=state["selected"] if state else 0)
        self.mode = tk.StringVar(value=state["mode"] if state else "CC")
        self.channel = tk.StringVar(value=str(state["channel"]) if state else "1")
        self.orientation = tk.StringVar(value=state.get("orientation", "vertical") if state else "vertical")
        self.control_map = {}

        self.buttons = []
        self.button_data = state["buttons"] if state else [
            {"label": f"Option {i+1}", "control": i} for i in range(3)
        ]

        container = tk.Frame(self, bg=COL_FRAME)
        container.pack(fill="both", expand=True, padx=4, pady=4)

        for idx, btn in enumerate(self.button_data):
            label = btn["label"]
            value = idx
            control = btn["control"]
            self.control_map[value] = (label, control)

            rb = tk.Radiobutton(
                container,
                text=label,
                variable=self.selected,
                value=value,
                command=self.send_midi,
                indicatoron=0,
                font=BUTTON_FONT,
                bg=COL_BTN,
                fg=BUTTON_FG,
                selectcolor=COL_BTN_LATCHED,
                activebackground=COL_BTN_LATCHED,
                activeforeground=BUTTON_FG,
                relief="flat",
                bd=2,
                width=10,
                pady=10
            )

            if self.orientation.get() == "horizontal":
                rb.pack(side="left", padx=4, pady=4, fill="y", expand=True)
            else:
                rb.pack(side="top", padx=4, pady=4, fill="x", expand=True)

            self.buttons.append(rb)

        self.bind("<Button-3>", self.show_context_menu)
        for btn in self.buttons:
            btn.bind("<Button-3>", self.show_context_menu)

    def select_index_external(self, idx: int):
        """Programmatically select without sending MIDI (no echo)."""
        self.selected.set(idx)
        # Radiobuttons reflect IntVar automatically

    def set_from_midi(self, control_number: int):
        """Select the radio whose mapped control/note matches."""
        for idx, (_label, ctrl) in self.control_map.items():
            if ctrl == int(control_number):
                self.select_index_external(idx)
                break
    def send_midi(self):
        try:
            idx = self.selected.get()
            _, control = self.control_map[idx]
            value = 127
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
        menu = tk.Menu(self, tearoff=0, bg=COL_FRAME, fg=COL_TEXT, activebackground=COL_ACCENT)
        menu.add_command(label="Edit Group Setup", command=lambda: open_radio_group_setup(self))
        menu.add_command(label="Duplicate", command=lambda: duplicate(self))
        menu.add_command(label="Delete", command=lambda: self.master.destroy())
        menu.tk_popup(event.x_root, event.y_root)

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

    frame.bind("<Button-3>", lambda e: radio_group.show_context_menu(e))
    radio_group.bind("<Button-3>", lambda e: radio_group.show_context_menu(e))

    radio_groups.append({"frame": frame, "group": radio_group})
    root.after_idle(update_scroll_region)

def add_slider(state=None):
    frame = DraggableResizableFrame(scrollable_frame, bg=COL_FRAME, bd=2, relief="ridge")

    if state:
        x, y = state.get("x", 10), state.get("y", 10)
        w, h = state.get("width", DEFAULT_WIDTH), state.get("height", DEFAULT_HEIGHT_SLIDER)
    else:
        x, y, w, h = get_spawn_geometry(sliders, DEFAULT_HEIGHT_SLIDER)

    frame.place(x=x, y=y, width=w, height=h)
    print("Slider placed at:", x, y, "size:", w, h)

    # --- container (tight padding) ---
    container = tk.Frame(frame, bg=COL_FRAME)
    container.pack(fill="both", expand=True, padx=1, pady=1)
    container.pack_propagate(False)

    # grid: header, value label, slider
    container.grid_rowconfigure(0, weight=0)
    container.grid_rowconfigure(1, weight=0)
    container.grid_rowconfigure(2, weight=1)
    container.grid_columnconfigure(0, weight=1)

    # state vars
    mode_var    = tk.StringVar(value=state["mode"]    if state else "CC")
    channel_var = tk.StringVar(value=str(state["channel"]) if state else "1")
    control_var = tk.StringVar(value=str(state["control"]) if state else "1")
    name_var    = tk.StringVar(value=state.get("name", "Slider") if state else "Slider")

    # header
    name_entry = tk.Entry(
        container, textvariable=name_var, font=("Helvetica", 12, "bold"),
        bg=COL_FRAME, fg=COL_SLIDER_NAME, insertbackground=COL_SLIDER_NAME,
        relief="flat", highlightthickness=0, justify="center"
    )
    name_entry.grid(row=0, column=0, pady=0, sticky="we")

    # value label
    value_var = tk.StringVar()
    value_label = tk.Label(container, textvariable=value_var,
                           font=("Helvetica", 10), bg=COL_FRAME, fg=COL_SLIDER_VALUE)
    value_label.grid(row=1, column=0, pady=0, sticky="we")

    # the scale (no fixed length; tight padding)
    val_slider = tk.Scale(
        container, from_=127, to=0, orient=tk.VERTICAL,
        sliderlength=32,  # smaller thumb
        font=("Helvetica", 24),
        troughcolor=COL_BG, fg=COL_ACCENT, bg=COL_FRAME,
        highlightthickness=0, bd=0, activebackground=COL_ACCENT,
        showvalue=0
    )
    val_slider.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)

    # init value
    if state:
        val_slider.set(state.get("value", 0))
        value_var.set(state.get("value", 0))
    else:
        value_var.set(0)

    def update_val(val, ch=channel_var, ctrl=control_var, mode=mode_var):
        value_var.set(val)
        send_midi(val, ch, ctrl, mode)

    val_slider.config(command=update_val)

    # track slider entry
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

    # context menu bindings
    frame.bind("<Button-3>",      lambda e, s=slider_entry: show_context_menu(e, s))
    container.bind("<Button-3>",  lambda e, s=slider_entry: show_context_menu(e, s))
    name_entry.bind("<Button-3>", lambda e, s=slider_entry: show_context_menu(e, s))
    value_label.bind("<Button-3>",lambda e, s=slider_entry: show_context_menu(e, s))
    val_slider.bind("<Button-3>", lambda e, s=slider_entry: show_context_menu(e, s))

    # 🔧 size it NOW so you get the tight look immediately
    resize_slider(slider_entry)
    # and once Tk finishes laying out
    root.after_idle(lambda: resize_slider(slider_entry))

    root.after_idle(update_scroll_region)
    print("🟩 Spawning slider:", state)


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
    print("Button placed at:", x, y, "size:", w, h)

    button = MidiButtonFrame(frame, state)
    button.pack(fill="both", expand=True, padx=4, pady=4)

    buttons.append(button)

    frame.bind("<Button-3>", lambda e: button.show_context_menu(e))
    root.after_idle(update_scroll_region)
    print("🟩 Spawning button:", state)

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

        self._drag_data   = {"x": 0, "y": 0}
        self._resize_data = {"x": 0, "y": 0, "w": 0, "h": 0, "active": False}

        self.grip = tk.Label(
            self,
            text="",
            font=("Helvetica", 1),
            bg=COL_FRAME,
            fg=COL_FRAME,
            width=2,
            height=1,
            cursor="bottom_right_corner",
            bd=0,
            highlightthickness=0,
            padx=4,
            pady=4
        )
        self.grip.place(relx=1.0, rely=1.0, anchor="se", x=0, y=0)
        self.grip.lower()
        self.grip.bind("<ButtonPress-1>", self.start_resize)
        self.grip.bind("<B1-Motion>", self.do_resize)
        self.grip.bind("<ButtonRelease-1>", self.stop_resize)

        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)
        self.bind("<ButtonRelease-1>", self.snap_to_grid)

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
        self.after_idle(update_scroll_region)

    def snap_to_grid(self, event):
        if self._resize_data["active"]:
            return
        x = round(self.winfo_x() / GRID_SIZE) * GRID_SIZE
        y = round(self.winfo_y() / GRID_SIZE) * GRID_SIZE
        self.place(x=x, y=y)
        self.after_idle(update_scroll_region)

    def start_resize(self, event):
        if locked.get():
            return
        self._resize_data.update({
            "active": True,
            "x": event.x_root,
            "y": event.y_root,
            "w": self.winfo_width(),
            "h": self.winfo_height()
        })

    def do_resize(self, event):
        if not self._resize_data["active"]:
            return
        dx = event.x_root - self._resize_data["x"]
        dy = event.y_root - self._resize_data["y"]
        new_w = max(MIN_WIDTH, round((self._resize_data["w"] + dx) / GRID_SIZE) * GRID_SIZE)
        new_h = max(MIN_HEIGHT, round((self._resize_data["h"] + dy) / GRID_SIZE) * GRID_SIZE)
        self.place(width=new_w, height=new_h)
        self.after_idle(update_scroll_region)

        for widget in self.winfo_children():
            if isinstance(widget, tk.Frame):
                for subwidget in widget.winfo_children():
                    if isinstance(subwidget, tk.Scale) and hasattr(subwidget, "_slider_entry_ref"):
                        resize_slider(subwidget._slider_entry_ref)

    def stop_resize(self, event):
        self._resize_data["active"] = False
        self.after_idle(update_scroll_region)

# ---------------- Slider helpers ----------------
def resize_slider(slider_entry):
    container   = slider_entry["container"]
    slider      = slider_entry["slider"]
    name_entry  = slider_entry["name_entry"]

    container.update_idletasks()

    # actual header + value label heights
    name_h = name_entry.winfo_reqheight()
    value_label = None
    for w in container.grid_slaves(row=1, column=0):
        value_label = w
        break
    value_h = value_label.winfo_reqheight() if value_label else 0

    reserved = name_h + value_h  # no extra padding baked in
    height   = container.winfo_height()
    width    = container.winfo_width()

    slider_length = max(20, height - reserved)
    slider.config(length=slider_length, width=max(30, int(width)))

    # keep the resize grip visible
    slider_entry["frame"].grip.lift()

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
    slider_entry["frame"].destroy()
    sliders.remove(slider_entry)

# ---------------- MIDI ----------------
def open_midi_setup(slider_entry):
    win = tk.Toplevel(root)
    win.title("MIDI Setup")
    win.configure(bg=COL_FRAME)
    win.geometry("200x120")
    font_label = ("Helvetica", 10, "bold")

    tk.Label(win, text="Mode", font=font_label, bg=COL_FRAME, fg=COL_TEXT).grid(row=0, column=0, sticky="e", padx=8, pady=6)
    ttk.Combobox(win, textvariable=slider_entry["mode"],
                 values=["CC", "Note", "Pitch Bend", "Aftertouch"],
                 state="readonly", width=10).grid(row=0, column=1, sticky="w", padx=8, pady=6)

    tk.Label(win, text="Channel", font=font_label, bg=COL_FRAME, fg=COL_TEXT).grid(row=1, column=0, sticky="e", padx=8, pady=6)
    ttk.Combobox(win, textvariable=slider_entry["channel"],
                 values=[str(i) for i in range(1, 17)],
                 state="readonly", width=4).grid(row=1, column=1, sticky="w", padx=8, pady=6)

    tk.Label(win, text="cc/note", font=font_label, bg=COL_FRAME, fg=COL_TEXT).grid(row=2, column=0, sticky="e", padx=8, pady=6)
    ttk.Combobox(win, textvariable=slider_entry["control"],
                 values=[str(i) for i in range(0, 128)],
                 state="readonly", width=5).grid(row=2, column=1, sticky="w", padx=8, pady=6)

    tk.Button(win, text="Close", command=win.destroy,
              bg=COL_ACCENT, fg=COL_TEXT, font=("Helvetica", 10, "bold"),
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
                    # Allow the types we handle
                    if msg.type not in ("control_change", "note_on", "note_off", "pitchwheel", "aftertouch"):
                        continue

                    # ---------- SLIDERS (existing) ----------
                    for entry in sliders:
                        mode = entry["mode"].get()
                        ch = int(entry["channel"].get()) - 1
                        ctrl = int(entry["control"].get())
                        if msg.channel != ch:
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

                    # ---------- BUTTONS (NEW) ----------
                    for btn in buttons:
                        mode = btn.mode.get()
                        ch = int(btn.channel.get()) - 1
                        ctrl = int(btn.control.get())
                        if msg.channel != ch:
                            continue
                        if msg.type == "control_change" and mode == "CC" and msg.control == ctrl:
                            btn.set_from_midi(msg.value)
                        elif msg.type == "note_on" and mode == "Note" and msg.note == ctrl:
                            btn.set_from_midi(msg.velocity)
                        elif msg.type == "note_off" and mode == "Note" and msg.note == ctrl:
                            btn.set_from_midi(0)
                        elif msg.type == "aftertouch" and mode == "Aftertouch":
                            # Treat aftertouch value like a momentary amount
                            btn.set_from_midi(msg.value)

                    # ---------- RADIO GROUPS (NEW) ----------
                    for rg in radio_groups:
                        group = rg["group"]
                        mode = group.mode.get()
                        ch = int(group.channel.get()) - 1
                        if msg.channel != ch:
                            continue
                        if msg.type == "control_change" and mode == "CC":
                            # choose by control number
                            group.set_from_midi(msg.control)
                        elif msg.type == "note_on" and mode == "Note":
                            # choose by note number
                            group.set_from_midi(msg.note)
                        # note_off not needed for radio selection (selection is sticky)
        except Exception as e:
            print("MIDI input error:", e)


    threading.Thread(target=midi_loop, daemon=True).start()

def select_port():
    global midi_out
    if midi_out:
        midi_out.close()
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
        button.master.destroy()
    buttons.clear()

    for rg in radio_groups[:]:
        rg["frame"].destroy()
    radio_groups.clear()

    for widget in scrollable_frame.winfo_children():
        if isinstance(widget, DraggableResizableFrame):
            widget.destroy()

    for item in data.get("widgets", []):
        widget_type = item.get("type")
        if widget_type == "slider":
            add_slider(item)
        elif widget_type == "button":
            add_midi_button(item)
        elif widget_type == "radio":
            add_radio_group(item)

    current_filename.set(file_path.split("/")[-1])
    root.title(f"MIDI Controller - {current_filename.get()}")
    print("Session loaded:", file_path)

    update_scroll_region()
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

# Optional: auto-spawn one control so the window is never blank.
# Comment this out if you don’t want default content.
root.after(50, add_slider)

# Or, if you prefer to prompt loading a file at start:
# root.after(100, load_state)

root.mainloop()
