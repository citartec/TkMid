# TkMid - Coming Soon
Touchscreen Midi controller software

Tkinter MIDI Controller

This is a fully customizable MIDI controller built using Python and Tkinter. It allows you to create, move, resize, and configure sliders and buttons that send real-time MIDI messages. The app supports MIDI input syncing, latch-mode buttons, and saving/loading complete layouts.
Features

Customizable Widgets

    Vertical sliders with named labels and value display

    Buttons with momentary or latch behavior

    All widgets support MIDI modes: Control Change (CC), Note On, Pitch Bend, and Aftertouch

Real-Time MIDI Output

    Sends MIDI messages using the mido library

    Adjustable MIDI channel and control number per widget

External MIDI Input Support

    Incoming messages update sliders in real-time based on matching channel and control

Drag-and-Resize Interface

    Widgets are freely positionable and resizable within a grid-snapped canvas

    Lock/unlock controls to prevent accidental repositioning

Session Management

    Save and load full configurations as JSON files

    Widget positions, sizes, labels, and MIDI mappings are preserved

    Automatically loads the last session at startup

Context Menus

    Right-click widgets to access setup, duplicate, rename, or delete options

    Right-click background to add new sliders or buttons, or change MIDI ports

Requirements

    Python 3.7+

    Tkinter (usually included with Python)

    mido Python package

Install dependencies:

pip install mido python-rtmidi





















