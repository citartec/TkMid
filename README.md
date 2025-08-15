MidTk - A Python-based MIDI controller GUI.

<img width="1256" height="665" alt="image" src="https://github.com/user-attachments/assets/bf220d8c-3526-4561-a93a-91c1e0f01f85" />

https://github.com/user-attachments/assets/b7568fcd-7d10-422b-a276-5920cdd2e831

Overview
--------
MidTk lets you build and customize your own MIDI controller using sliders, buttons, and radio button groups.
All elements can be resized, positioned, grouped, saved, and reloaded.
-
How to use
----------
Right click on the background to create, save, load, select midi port and lock controls. Another right click on the sliders, buttons, radio group and group boxes will bring up the midi options and group options. 

If you right click then click unlock controls, it will bring up resize options and you can move things around. 
<img width="1256" height="665" alt="Screenshot from 2025-08-14 17-09-20" src="https://github.com/user-attachments/assets/2817f9da-e888-4f3a-87a5-6b599fc976a5" />

Groups
-------
Group boxes are used to group sliders, buttons and radio buttons. While unlock controls is selected you can drag these boxes over a layout you want to group and then press "recompute members" to create a group and use "recompute members" any time you want to add things to the group. You can also Duplicate groups.

Requirements
------------

Python 3.11.13

pip install mido

pip install python-rtmidi

Then run the python file,

python3 MidTk0.4.5.py
