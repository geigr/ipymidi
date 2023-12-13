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


_ACTIVE_EVENTS: dict[str, "MIDIEvent"] = {}


def format_input(props: dict, indent=4) -> str:
    lines = []
    for key, value in props.items():
        lines.append(f"{key}: {value}")
    return textwrap.indent("\n".join(lines), " " * indent)


class MIDIInterface(anywidget.AnyWidget):
    """Singleton class representing the (Web) MIDI interface as a widget.

    Do not instantiate this class directly. Instead, access to the interface
    is done via :py:func:`get_interface`.

    """

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

    def __new__(cls):
        if MIDIInterface._singleton is None:
            MIDIInterface._singleton = super().__new__(cls)
        return MIDIInterface._singleton

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
            "args": {
                "target_type": target_type,
                "target_id": target_id,
                "event_model_id": event.model_id,
                "event_name": event_name,
                "event_props": event_props,
                "event_id": event_id,
            }
        }
        self.send(command)

        _ACTIVE_EVENTS[event_id] = event
        return event

    def _remove_event(self, event_id):
        if event_id not in _ACTIVE_EVENTS:
            raise KeyError(f"no active MIDI event of id {event_id!r} to remove")
        self.send({"action": "remove_listener", "args": {"event_id": event_id}})
        _ACTIVE_EVENTS.pop(event_id)

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

    _id = tt.Unicode().tag(sync=True)
    _target_obj: Any
    _target_id = tt.Unicode(allow_none=True).tag(sync=True)
    _target_type = tt.Enum(("webmidi", "input")).tag(sync=True)
    _name = tt.Unicode().tag(sync=True)
    _prop_names = tt.List(tt.Unicode()).tag(sync=True)

    enabled = tt.Bool(True)

    def __init__(self, target: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._target_obj = target

        traits = {}
        for pn in self._prop_names:
            trait = EVENT_TRAITS[target._type][self._name][pn]
            trait.read_only = True
            traits[pn] = trait.tag(sync=True)

        self.add_traits(**traits)

    @property
    def target(self) -> Any:
        """Object that dispatched the MIDI event."""
        return self._target_obj

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
        get_interface()._remove_event(self._event_id)

    def close(self):
        self.untrack()
        super().close()


class Inputs(collections.abc.Sequence):
    """A sequence of all available MIDI input devices.

    This class is not a widget. It is a proxy to all the input devices that are
    syncronized via :py:class:`MIDIInterface`.

    """

    @property
    def _inputs(self) -> list[dict[str, str]]:
        # prevent this object getting out-of-sync with MIDIInterface._inputs
        # (do not copy and store any mutable state)
        return get_interface()._inputs

    def __getitem__(self, key: int | str) -> "Input":
        inputs = self._inputs

        idx = -1
        if isinstance(key, int):
            idx = key
        elif isinstance(key, str):
            for i, props in enumerate(inputs):
                if key == props["id"] or key == props["name"]:
                    idx = i
                    break
            if idx == -1:
                raise KeyError(f"no MIDI input device with name or id {key!r}")
        else:
            raise ValueError(
                "MIDI input device must be either a integer (index) or a string (id or name)"
            )

        return Input(idx)

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
        inputs = self._inputs
        lines = [f"MIDI Inputs ({len(inputs)})"]
        for i, props in enumerate(inputs):
            lines.append(f"{i}:")
            lines.append(format_input(props))
        return "\n".join(lines)


class Input:
    """A MIDI input device.

    This class is not a widget. It is a proxy to the input device that is
    synchronized via :py:class:`MIDIInterface`.

    This proxy may eventually become out-of-sync with the MIDI interface (e.g.,
    when the corresponding input device has been unplugged), in which case the
    properties of this object become frozen (their value won't be updated).

    """

    _type = "input"
    _idx: int
    _props_cached: dict[str, Any]

    def __init__(self, idx: int):
        self._idx = idx
        self._synced = True

        # fill cache
        self._props_cached = {}
        props_cached = self._props
        self._props_cached = props_cached

    @property
    def _props(self) -> dict[str, Any]:
        # prevent this object getting out-of-sync with MIDIInterface._inputs
        # (do not copy and store any mutable state)
        inputs = get_interface()._inputs

        if not self._props_cached:
            # 1st call in __init__ (synced)
            return inputs[self._idx]
        elif self._idx >= len(inputs):
            # index out of range (not synced)
            return self._props_cached
        elif inputs[self._idx]["id"] == self._props_cached["id"]:
            # unchanged id (synced)
            self._props_cached = inputs[self._idx]
            return inputs[self._idx]
        else:
            # changed id (not synced)
            return self._props_cached

    @property
    def synced(self) -> bool:
        """Return True if this object (proxy) is still synced with the MIDI interface."""
        inputs = get_interface()._inputs

        if self._idx >= len(inputs):
            # index out of range
            return False
        else:
            return inputs[self._idx]["id"] == self._props_cached["id"]

    def _check_synced(self):
        if not self.synced:
            return ValueError(
                "This input is out-of-sync with the MIDI interface "
                f"(likely because the corresponding device {self.name!r}) "
                "has been unplugged)"
            )

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
        self._check_synced()

        event_id = str(uuid.uuid4())

        return MIDIEvent(
            self,
            _id=event_id,
            _name=name,
            _prop_names=properties,
            _target_type="input",
            _target_id=self.id,

        )

    def __repr__(self) -> str:
        return f"MIDI Input [{self._idx}]\n{format_input(self._props)}"
