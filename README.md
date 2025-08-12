# Midtk
<img width="727" height="652" alt="image" src="https://github.com/user-attachments/assets/14a39f5d-55e2-4a0d-b600-b55358cc7dd7" />
<img width="640" height="573" alt="image" src="https://github.com/user-attachments/assets/8d4335cd-cb93-4fb7-80e2-dbcf78a916ba" />

A Tkinter-based virtual MIDI controller that lets you create, drag, resize, and configure sliders, buttons, and radio groups for real-time MIDI control.
All widgets can now send and receive MIDI messages, meaning they update in real time when matching messages are received from an external MIDI device. 

Will run on any Linux and Windows that has Python installed. Will also run on the Raspberry Pi OS, i've not tired Mac but most likely if you install python

Left click on the edge of widgets to move them, they will snap to a grid.  
Right click on the widgets to get midi options and other things (Radio buttons need a right click on the actual buttons)
Right click on the background to create new sliders, buttons, set midi in and out. 


Features

    Spawnable widgets

        Sliders – Send and receive CC, Note, Pitch Bend, or Aftertouch.

        Buttons – Latch or momentary mode.

        Radio Groups – Mutually exclusive buttons, now auto-select when matching MIDI messages arrive.

    Drag & resize controls with grid snapping.

    Scrollable, zoomable canvas with large touch-friendly scrollbars.

    Context menus (right-click) for configuration, duplication, or deletion.

    Save/load setups to JSON (keeps widget positions, sizes, and settings).

    Full MIDI input sync for sliders, buttons, and radio groups.

    Customizable colors & UI constants at the top of the script.

Requirements

    Python 3.8+

    mido

    python-rtmidi (or other mido backend)

    Tkinter (usually included with Python)

Install dependencies:

pip install mido python-rtmidi

Usage

Run the app:

python MidTk0.4.py

On launch:

    A default slider is spawned (can be disabled in code).

    Right-click the background to:

        Add Slider, Button, or Radio Group

        Save/Load Setup

        Lock/Unlock Controls

        Select MIDI Input/Output ports

Widget Details
Sliders

    Sends MIDI on movement.

    Updates when matching external MIDI messages are received.

    Supports:

        CC

        Note

        Pitch Bend (full ±8192 range mapped to 0–127)

        Aftertouch

Buttons

    Latch mode – toggles on/off when triggered.

    Momentary mode – active while pressed or while incoming value > 0.

    Now update from external MIDI input:

        CC: follows value (≥64 = ON in latch mode)

        Note On/Off: momentary or latch toggle

        Aftertouch: momentary intensity

Radio Groups

    One selected button at a time.

    Vertical or horizontal layout.

    Now auto-select when receiving matching CC/Note for one of its buttons.

Saving & Loading

    Save Setup – Saves all widgets, positions, sizes, and MIDI settings to .json.

    Load Setup – Restores saved layout and settings.

    Found in right-click background menu.

MIDI Input Sync Logic

    Sliders – Update value directly from matching incoming CC/Note/Pitch Bend/Aftertouch.

    Buttons – Follow CC or Note On/Off values, latch or momentary as configured.

    Radio Groups – Selects the option with a control/note number matching the incoming MIDI message.

Shortcuts & Interactions

    Right-click background → Add widgets, save/load, lock/unlock, change ports.

    Right-click widget → Configure MIDI, rename, duplicate, delete.

    Drag to move; bottom-right corner grip to resize.

    Grid snapping keeps layout tidy.

Notes

    Ensure a valid MIDI output port is selected to send messages.

    External MIDI sync works for all widget types.

    The app uses JSON for state persistence.

License

MIT License – free to use and modify.


To run on a Raspberry Pi you need to create a new python env

python3 -m venv midtk

source midtk/bin/activate

python3 tkmid.py

Make sure you lock the canvas when using as touchscreen. 

If you create a bunch of sliders, make sure to change the cc numbers before touching the sliders or a feedback loop will start. 

This happens if you are sending the midi internally and not to an outside source. 
