import pathlib
from collections.abc import Mapping
from typing import Any, Iterable, Literal

import anywidget
import traitlets as tt

from ipymidi.event_traits import EVENT_TRAITTYPES


class MIDIEvent(anywidget.AnyWidget):
    """A widget tracking a specific MIDI event.

    Do not instantiate this class directly. Instead, create new instances
    via :py:meth:`Input.track_event`.

    Every instance has invariant properties (``name``, ``target``,
    ``prop_names``) as well as user-defined synchronized traits that correspond
    to the event properties to track. Two additional traits are always defined:

    - ``count`` (read-only): number of times the MIDI event has been captured
      by the widget.
    - ``enabled`` (read/write): can be used to temporarly disable tracking the
      MIDI event (enabled by default).

    """

    _esm = pathlib.Path(__file__).parent / "static" / "index.js"
    _anywidget_name = tt.Unicode("MIDIEvent", read_only=True).tag(sync=True)

    _all_events: list["MIDIEvent"] = []

    _target_obj: Any
    _target_id = tt.Unicode(allow_none=True).tag(sync=True)
    _target_type = tt.Enum(("interface", "input")).tag(sync=True)
    _name = tt.Unicode().tag(sync=True)
    _prop_names = tt.List(tt.Unicode()).tag(sync=True)

    enabled = tt.Bool(True, help="whether or not the MIDI event is tracked").tag(sync=True)

    count = tt.Int(
        0,
        read_only=True,
        help="Number of times the event has been captured since the creation of this object",
    ).tag(sync=True)

    def __init__(
        self,
        name: str,
        target: Any,
        target_type: Literal["interface", "input"],
        target_id: str | None = None,
        properties: Iterable[str] | Mapping[str, tt.TraitType] | None = None,
        **kwargs,
    ):
        super().__init__(
            _name=name,
            _target_obj=target,
            _target_id=target_id,
            _target_type=target_type,
            **kwargs,
        )

        # add user-defined event traits
        traits: dict[str, tt.TraitType]
        if properties is None:
            traits = EVENT_TRAITTYPES[target_type][name]
        elif isinstance(properties, Mapping):
            traits = dict(properties)
        else:
            traits = {k: EVENT_TRAITTYPES[target_type][name][k] for k in properties}

        for k, v in traits.items():
            v.read_only = True
            traits[k] = v.tag(sync=True)

        self._prop_names = list(traits)
        self.add_traits(**traits)

        # register event
        type(self)._all_events.append(self)

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

    @classmethod
    def close_all(cls):
        """Close all MIDIEvent widgets."""
        for e in cls._all_events:
            e.close()
