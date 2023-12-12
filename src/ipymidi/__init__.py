import collections.abc
import importlib.metadata
import pathlib
import textwrap
from typing import Literal

import anywidget
import traitlets as tt

try:
    __version__ = importlib.metadata.version("ipymidi")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"


InputConnection = tt.Enum(["pending", "open", "closed"])
InputState = tt.Enum(["connected", "disconnected"])
InputProps = tt.Dict(
    per_key_traits={
        "id": tt.Unicode(),
        "name": tt.Unicode(),
        "manufacturer": tt.Unicode(),
        "connection": InputConnection,
        "state": InputState,
    },
)


def format_input(props: dict, indent=4) -> str:
    lines = []
    for key, value in props.items():
        lines.append(f"{key}: {value}")
    return textwrap.indent("\n".join(lines), " " * indent)


class WebMidi(anywidget.AnyWidget):
    _singleton = None
    _view_name = tt.Any(None).tag(sync=True)
    _esm = pathlib.Path(__file__).parent / "static" / "widget.js"
    enabled = tt.Bool(False, read_only=True).tag(sync=True)

    _inputs = tt.List(InputProps, read_only=True).tag(sync=True)

    def __new__(cls):
        if WebMidi._singleton is None:
            WebMidi._singleton = super().__new__(cls)
        return WebMidi._singleton

    def enable(self):
        self.send({"action": "enable"})

    def _check_enabled(self):
        if not self.enabled:
            raise ValueError("MIDI is not enabled!")

    @property
    def inputs(self):
        self._check_enabled()
        return Inputs()


def get_midi():
    return WebMidi()


class Inputs(collections.abc.Sequence):
    """All available MIDI input devices."""

    _webmidi: WebMidi
    _inputs: list[dict[str, str]]

    def __init__(self):
        self._webmidi = get_midi()
        self._inputs = self._webmidi._inputs
        self._names = None

    def __getitem__(self, key: int | str) -> "Input":
        idx = -1
        if isinstance(key, int):
            idx = key
        elif isinstance(key, str):
            for i, props in enumerate(self._inputs):
                if key == props["id"] or key == props["name"]:
                    idx = i
                    break
            if idx == -1:
                raise KeyError(f"no MIDI input device with name or id {key!r}")
        else:
            raise ValueError(
                "MIDI input device must be either a integer (index) or a string (id or name)"
            )

        return Input(idx, self._inputs[idx])

    def __len__(self):
        return len(self._inputs)
    
    @property
    def names(self) -> list[str]:
        """Returns the names of the MIDI input devices."""
        return [props["name"] for props in self._inputs]

    @property
    def ids(self) -> list[str]:
        """Returns the ids of the MIDI input devices."""
        return [props["id"] for props in self._inputs]

    def __repr__(self) -> str:
        lines = [f"MIDI Inputs ({len(self._inputs)})"]
        for i, props in enumerate(self._inputs):
            lines.append(f"{i}:")
            lines.append(format_input(props))
        return "\n".join(lines)


class Input:
    """A MIDI input device."""

    _webmidi: WebMidi

    def __init__(self, idx: int, props: dict):
        self._webmidi = get_midi()
        self._idx = idx
        self._props = props

    @property
    def name(self) -> str:
        """MIDI input device name."""
        return self._props["name"]

    @property
    def id(self) -> str:
        """MIDI input device id.

        The id may differ from one platform to another.

        """
        return self._props["id"]

    @property
    def manufacturer(self) -> str:
        """MIDI input device manufacturer."""
        return self._props["manufacturer"]

    @property
    def connection(self) -> Literal["pending", "open", "closed"]:
        """MIDI input device port's connection state."""
        return self._props["connection"]

    @property
    def state(self) -> Literal["connected", "disconnected"]:
        """MIDI input device port's state."""
        return self._props["state"]

    def __repr__(self) -> str:
        return f"MIDI Input [{self._idx}]\n{format_input(self._props)}"
