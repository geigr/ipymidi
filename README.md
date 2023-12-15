![logo](https://user-images.githubusercontent.com/4160723/290532327-283f5234-2f8c-4b4e-9e59-79b9551f11d0.svg)

# IpyMIDI

_Interactive MIDI in Jupyter_

IpyMIDI exposes the Web MIDI interface ([Web MIDI
API](https://developer.mozilla.org/en-US/docs/Web/API/Web_MIDI_API)) to Python
as [Jupyter widgets](https://ipywidgets.readthedocs.io) via
[WEBMIDI.js](https://webmidijs.org/). Connect your MIDI devices (e.g., keyboards,
controllers, etc.) and start interacting with them in Jupyter!

**Note: this is very much work in progress (nothing much to see yet)!**

## Usage Example

Create a Jupyter notebook and import the library.

```python
import ipymidi
```

Get access to the Web MIDI interface.

```python
midi = ipymidi.get_interface()
```

Enable the MIDI interface (your Web browser may ask you the permission to access it).

```python
midi.enable()
```

Get the list of all connected MIDI input devices.

```python
midi.inputs
```

```
MIDI Inputs (2)
0:
    id: 92212230
    name: Virtual MIDI
    manufacturer: Apple Inc.
    connection: open
    state: connected
1:
    id: -1491552641
    name: Arturia KeyStep 37
    manufacturer: Arturia
    connection: open
    state: connected
```

Track a specific MIDI event emitted from one input device (e.g., the "noteon"
event emitted from a MIDI keyboard).

```python
ev = midi.inputs["Arturia KeyStep 37"].track_event("noteon", ["note_identifier"])
```

Use the `ev` object like any other Jupyter widget, e.g., to print in an output
widget the MIDI note that has just been played on the input device.

```python
import ipywidgets

output = ipywidgets.Output()

@ev.observe
def print_message(change):
    output.clear_output()
    with output:
        print(f"Note {change["owner"].note_identifier} played!")

output
```
