![logo](https://user-images.githubusercontent.com/4160723/290532327-283f5234-2f8c-4b4e-9e59-79b9551f11d0.svg)

# IpyMIDI

_Interactive MIDI in Jupyter_

IpyMIDI exposes the Web browsers' [MIDI](https://en.wikipedia.org/wiki/MIDI)
support to Python as [Jupyter widgets](https://ipywidgets.readthedocs.io)
via the [WEBMIDI.js](https://webmidijs.org/) Javascript library. Connect your
MIDI devices (e.g., keyboards, controllers, etc.) and start interacting with
them in Jupyter!

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
keyboard = midi.inputs["Arturia KeyStep 37"]
noteon_event = keyboard.add_listener("noteon", ["note_identifier"])
```

Use the `noteon_event` object like any other Jupyter widget, e.g., to print in
an output widget the MIDI note that has just been played by the input device.

```python
import ipywidgets

output = ipywidgets.Output()

@noteon_event.observe
def print_message(change):
    output.clear_output()
    with output:
        print(f"Note {change["owner"].note_identifier} played!")

output
```
