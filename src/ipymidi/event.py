import pathlib
from typing import Any

import anywidget
import traitlets as tt

from ipymidi.event_traits import EVENT_TRAITS


class MIDIEvent(anywidget.AnyWidget):
    """A widget tracking a specific MIDI event.

    Do not instantiate this class directly. Instead, create new instances
    via :py:meth:`Input.track_event`.

    """
    _esm = pathlib.Path(__file__).parent / "static" / "index.js"
    _anywidget_name = tt.Unicode("MIDIEvent", read_only=True).tag(sync=True)

    _target_obj: Any
    _target_id = tt.Unicode(allow_none=True).tag(sync=True)
    _target_type = tt.Enum(("webmidi", "input")).tag(sync=True)
    _name = tt.Unicode().tag(sync=True)
    _prop_names = tt.List(tt.Unicode()).tag(sync=True)

    enabled = tt.Bool(True).tag(sync=True)

    count = tt.Int(
        0,
        read_only=True,
        help="Number of times the event has been captured since the creation of this object",
    ).tag(sync=True)

    timestamp = tt.Float(
        help="The moment when the event occurred (ms)",
        read_only=True,
    ).tag(sync=True)

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
