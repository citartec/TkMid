MidTk

A Python-based MIDI controller GUI.

Overview

MidTk lets you build and customize your own MIDI controller using sliders, buttons, and radio button groups.
All elements can be resized, positioned, grouped, saved, and reloaded.
It works with any MIDI-compatible device and can both send and receive MIDI messages.

Features

SlidersMidTk

MidTk is a flexible, Python-based MIDI controller application that lets you design your own control surface exactly the way you want it. Whether you need sliders, buttons, or radio button groups, you can create, position, and resize each element to fit your workflow. Every control is fully configurable, allowing you to set MIDI channels, CC numbers, notes, pitch bend, aftertouch, and custom labels.

Sliders give you precise control over parameters and can be assigned to any supported MIDI message type. Buttons can be set to momentary or latch modes, perfect for triggering samples, toggling effects, or switching states. Radio button groups are ideal for selecting between mutually exclusive settings, such as synth waveforms—MidTk automatically assigns the correct values to each button based on the number of options.

To organize complex layouts, you can group controls into a movable, resizable group box. Groups can be duplicated in seconds, making it easy to build multiple sections with consistent settings. Once your layout is complete, you can save it for later use or reload previous setups instantly.

MidTk automatically detects connected MIDI devices and works with any hardware or software that accepts MIDI input. It supports both sending and receiving MIDI, making it suitable for live performance, studio work, or hardware control. Although it runs perfectly inside a Conda environment, Conda is not required.

Requirements

Python 3.11.13

mido and python-rtmidi
Adjustable channel, CC number, note, pitch bend, aftertouch, and name.

Buttons

Adjustable channel, CC number, note, and name.

Supports momentary or latch modes.

Radio Button Groups

Adjustable channel, CC number, or note for the group.

Automatic value assignment based on the number of buttons.

Useful for parameter changes such as waveform selection.

Group Boxes

Group multiple controls together.

Duplicate and reposition groups.

Other

Save and load complete setups.

Auto-detects MIDI devices.

Real-time MIDI send and receive.

Requirements

Python 3.11.13

Python packages:
