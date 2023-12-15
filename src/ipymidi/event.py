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


class EventTrackerMixin:
    """Extends the MIDIInterface, Input, and InputChannel classes with the
    ability to track MIDI events.

    """

    _target_type: Literal["interface", "input"]

    @property
    def _target_id(self) -> str | None:
        return None

    @property
    def events(self) -> dict[str, dict[str, tt.TraitType]]:
        """Returns a dictionary of available MIDI events and their corresponding
        properties as trait types.

        Note that some events available in WEBMIDI.js may not yet be implemented
        in IpyMIDI.

        See Also
        --------
        :py:meth:`MIDIInterface.track_event`
        :py:meth:`Input.track_event`

        """
        return dict(EVENT_TRAITTYPES[self._target_type])

    def track_event(
        self,
        name: str,
        properties: Iterable[str] | Mapping[str, tt.TraitType] | None = None,
    ) -> MIDIEvent:
        """Track a MIDI event triggered from the MIDI interface or an input
        (channel) device.

        Parameters
        ----------
        name : str
            Name of the MIDI event.
        properties: sequence or dict-like, optional
            Either a list of the names of the event properties to track
            or a mapping of property names to :py:class:`traitlets.TraitType` objects.
            If ``None`` (default), all available properties for the MIDI event will be
            tracked. See the notes below for more details.

        Returns
        -------
        event : MIDIEvent
            A new widget with traits added for each of the
            given event properties. The values of those traits will be
            updated each time the event is triggered.

        See Also
        --------
        :py:attr:`MIDIInterface.events`
        :py:attr:`Input.track_events`

        Notes
        -----
        The names of the event and event properties must match their names as
        defined in WEBMIDI.js. Snake case is used by IpyMIDI while camel case is
        used by WEBMIDI.js (IpyMIDI takes care of converting from one format to
        the other).

        It is generally safer to provide event properties as a list of names: it
        will either work or raise an error on the Python side. Using a mapping
        is still useful in case an event available in WEBMIDI.js is still not
        implemented in IpyMIDI, but it might throw an error in the browser's
        Javascript console and/or not work properly on the Python side.

        """
        return MIDIEvent(
            name,
            self,
            target_type=self._target_type,
            target_id=self._target_id,
            properties=properties,
        )
