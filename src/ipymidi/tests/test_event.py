import pytest
import traitlets as tt

from ipymidi import Listener, get_interface
from ipymidi.event_traits import EVENT_TRAITTYPES
from ipymidi.interface import Inputs


def test_listener_init() -> None:
    midi = get_interface()
    listener = Listener("enabled", midi, "interface")

    assert listener.count == 0
    assert listener.suspended is False
    assert listener in Listener._all_listeners.values()

    assert listener.has_trait("timestamp")
    assert listener.traits()["timestamp"].read_only is True
    assert listener.traits()["timestamp"].metadata.get("sync") is True

    listener = Listener("enabled", midi, "interface", properties=["timestamp"])
    assert listener.has_trait("timestamp")
    listener = Listener("enabled", midi, "interface", properties={"timestamp": tt.Float()})
    assert listener.has_trait("timestamp")


def test_listener_properties() -> None:
    midi = get_interface()
    listener = Listener("enabled", midi, "interface")

    assert listener.target is midi
    assert listener.event == "enabled"
    assert listener.prop_names == ["timestamp"]


def test_listener_close() -> None:
    midi = get_interface()

    listener1 = Listener("enabled", midi, "interface")
    listener2 = Listener("connected", midi, "interface")

    listener1.close()
    assert listener1 not in Listener._all_listeners.values()
    assert listener2 in Listener._all_listeners.values()

    Listener.close_all()
    assert len(Listener._all_listeners) == 0


@pytest.fixture(scope="function")
def inputs_patched(monkeypatch: pytest.MonkeyPatch) -> Inputs:
    inputs = [
        {
            "id": "9999",
            "name": "Input Device",
            "manufacturer": "DIY",
            "connection": "open",
            "state": "connected",
        }
    ]
    midi = get_interface()
    monkeypatch.setattr(type(midi), "enabled", True)
    monkeypatch.setattr(type(midi), "_inputs", inputs)
    return midi.inputs


def test_event_mixin_events(inputs_patched) -> None:
    midi = get_interface()
    assert midi.events == EVENT_TRAITTYPES["interface"]
    assert inputs_patched[0].events == EVENT_TRAITTYPES["input"]


def test_event_mixin_listener(inputs_patched) -> None:
    midi = get_interface()
    input = inputs_patched[0]

    listener1 = midi.add_listener("enabled")
    listener2 = input.add_listener("noteon", ["note_identifier"])

    assert listener1 in midi.get_listeners()
    assert listener2 in input.get_listeners()
    assert listener1 not in input.get_listeners()
    assert listener2 in input.get_listeners(event="noteon")
