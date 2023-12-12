import collections.abc
import importlib.metadata
import pathlib
import uuid
import textwrap
from typing import Any, Literal

import anywidget
import traitlets as tt

from ipymidi.event_traits import EVENT_TRAITS

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


class MIDIInterface(anywidget.AnyWidget):
    """Singleton class representing the (Web) MIDI interface."""

    _type = "webmidi"
    _singleton = None
    _view_name = tt.Any(None).tag(sync=True)
    _esm = pathlib.Path(__file__).parent / "static" / "widget_interface.js"

    enabled = tt.Bool(
        False,
        read_only=True,
        help="Indicates whether access to the host's MIDI subsystem is granted or not"
    ).tag(sync=True)

    _inputs = tt.List(InputProps, read_only=True).tag(sync=True)

    _active_events: dict[str, "MIDIEvent"]

    def __new__(cls):
        if MIDIInterface._singleton is None:
            MIDIInterface._singleton = super().__new__(cls)
        return MIDIInterface._singleton

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._active_events = {}

    def enable(self):
        """Checks if the Web MIDI interface is available in the current
        environment and then tries to connect to the host's MIDI subsystem.

        This may show a security prompt in the Web browser asking for access to
        the MIDI devices.

        """
        self.send({"action": "enable"})

    def _check_enabled(self):
        if not self.enabled:
            raise ValueError("MIDI is not enabled!")

    def _add_event(
        self,
        target: Any,
        event_name: str,
        event_props: list[str],
    ):
        event_id = str(uuid.uuid4())
        target_type = target._type
        target_id = getattr(target, "id")

        event = MIDIEvent(event_id, target, event_name, event_props)

        command = {
            "action": "add_listener",
            "target_type": target_type,
            "target_id": target_id,
            "event_model_id": event.model_id,
            "event_name": event_name,
            "event_props": event_props,
            "event_id": event_id,
        }
        self.send(command)

        self._active_events[event_id] = event
        return event

    def _remove_event(self, event_id):
        if event_id not in self._active_events:
            raise KeyError(f"no active MIDI event of id {event_id!r} to remove")
        self.send({"action": "remove_listener", "id": event_id})

    @property
    def inputs(self) -> "Inputs":
        """Returns a sequence of MIDI input devices."""
        self._check_enabled()
        return Inputs()


def get_interface() -> MIDIInterface:
    """Return the MIDI interface object."""
    return MIDIInterface()


class MIDIEvent(anywidget.AnyWidget):
    """A widget tracking a specific MIDI event."""

    _esm = pathlib.Path(__file__).parent / "static" / "widget_event.js"

    _event_id: str
    _target: Any
    _name: str
    _prop_names: list[str]

    _interface: MIDIInterface

    def __init__(
        self,
        event_id: str,
        target: Any,
        name: str,
        prop_names: list[str]
    ):
        super().__init__()
        self._event_id = event_id
        self._target = target
        self._name = name
        self._prop_names = prop_names
        self._interface = get_interface()

        traits = {}
        for pn in prop_names:
            trait = EVENT_TRAITS[target._type][name][pn]
            trait.read_only = True
            traits[pn] = trait.tag(sync=True)

        self.add_traits(**traits)

    @property
    def target(self) -> Any:
        """Object that dispatched the MIDI event."""
        return self._target

    @property
    def name(self) -> str:
        """Name of the tracked MIDI event."""
        return self._name

    @property
    def prop_names(self) -> list[str]:
        """Names of the tracked MIDI event properties.

        Every property is exposed as a widget trait.
        """
        return self._prop_names

    def untrack(self):
        """Stop tracking the MIDI event.

        This operation cannot be reversed.
        """
        self._interface._remove_event(self._event_id)

    def close(self):
        self.untrack()
        super().close()


class Inputs(collections.abc.Sequence):
    """All available MIDI input devices."""

    _interface: MIDIInterface
    _inputs: list[dict[str, str]]

    def __init__(self):
        self._interface = get_interface()
        self._inputs = self._interface._inputs
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

    _type = "input"
    _interface: MIDIInterface

    def __init__(self, idx: int, props: dict):
        self._interface = get_interface()
        self._idx = idx
        self._props = props

        # TODO: props may become out-of-sync when the input state changes
        # -> figure out a way to avoid that

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

    def track_event(self, name: str, properties: list[str]) -> MIDIEvent:
        """Track a MIDI event triggered from this input device.

        Parameters
        ----------
        name : str
            Name of the MIDI event.
        properties: list
            A list of the names of the event properties to track.

        Returns
        -------
        event : MIDIEvent
            A new widget with traits added for each of the
            given event properties. The values of those traits will be
            updated each time the event is triggered.
        """
        return self._interface._add_event(self, name, properties)

    def __repr__(self) -> str:
        return f"MIDI Input [{self._idx}]\n{format_input(self._props)}"
