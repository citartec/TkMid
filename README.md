# TkMid -

A Tkinter-based virtual MIDI controller that lets you create, drag, resize, and configure sliders, buttons, and radio groups for real-time MIDI control.
All controls can send MIDI messages, receive external MIDI input, and be saved/loaded in a JSON configuration.
Features

    Spawnable widgets

        Sliders – Send CC, Note, Pitch Bend, or Aftertouch messages.

        Buttons – Latch or momentary mode, customizable MIDI settings.

        Radio Groups – Mutually exclusive buttons for waveform/type selection or other discrete values.

    Draggable & resizable controls with grid snapping.

    Context menus (right-click) for configuration, duplication, or deletion.

    Scrollable canvas with touch-friendly scrollbars.

    Save/load setups to .json (preserves widget positions, sizes, and settings).

    External MIDI input sync – Sliders update when receiving matching MIDI messages.

    Customizable colors & layout constants at the top of the script.

Requirements

    Python 3.8+

    mido

    A backend for mido (e.g., python-rtmidi)

    Tkinter (comes with most Python installs)

Install dependencies:

pip install mido python-rtmidi

Usage

Run:

python MidTk0.4.py

On launch:

    The app auto-creates a default slider (optional).

    Right-click the background to:

        Add Slider, Button, or Radio Group

        Save/Load Setup

        Lock/Unlock Controls

        Select MIDI Input/Output Ports

Controls
Sliders

    Editable name and MIDI settings.

    Sends MIDI on movement.

    Updates in real time when matching MIDI messages are received.

Buttons

    Momentary or latch mode.

    Customizable MIDI mode, channel, and control/note number.

Radio Groups

    One selected button at a time.

    Fully editable labels and MIDI mappings.

    Vertical or horizontal layout.

Saving & Loading

    Save Setup – Creates a JSON file with all widgets, their positions, sizes, and settings.

    Load Setup – Restores from a saved JSON.

    Both are accessible from the right-click background menu.

Shortcuts / Interactions

    Right-click a control → Configure, duplicate, or delete it.

    Drag by clicking and holding on a widget's frame.

    Resize using the small bottom-right corner grip.

    Grid snapping keeps layouts tidy.

Notes

    Make sure a valid MIDI output port is selected, or messages will not send.

    Pitch Bend sliders use full MIDI pitch range (-8192 to 8191) mapped to 0–127.

    External MIDI sync only affects sliders (buttons and radio groups do not respond yet).

License

MIT License – free to use and modify.















