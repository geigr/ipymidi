from copy import deepcopy
from textwrap import dedent

import pytest
from pytest_mock import MockerFixture

import ipymidi
from ipymidi.interface import Inputs


def test_interface_singleton() -> None:
    midi = ipymidi.get_interface()
    midi2 = ipymidi.get_interface()

    assert midi is midi2


def test_interface_enable(mocker: MockerFixture) -> None:
    midi = ipymidi.get_interface()

    # test disabled by default
    assert midi.enabled is False

    spy = mocker.spy(midi, "send")
    midi.enable()
    spy.assert_called_once_with({"command": "enable"})


def test_interface_inputs_no_enabled() -> None:
    midi = ipymidi.get_interface()

    with pytest.raises(ValueError, match="MIDI is not enabled!"):
        midi.inputs


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
    monkeypatch.setattr(type(ipymidi.get_interface()), "enabled", True)
    monkeypatch.setattr(type(ipymidi.get_interface()), "_inputs", inputs)
    return ipymidi.get_interface().inputs


def test_inputs_getitem(inputs_patched) -> None:
    for key in (0, "9999", "Input Device"):
        input = inputs_patched[key]
        assert input.id == "9999"

    with pytest.raises(KeyError, match="no MIDI input device"):
        inputs_patched["non-existent device"]

    with pytest.raises(ValueError, match="MIDI input device must be either"):
        inputs_patched[None]  # type: ignore


def test_inputs_properties(inputs_patched) -> None:
    assert len(inputs_patched) == 1
    assert inputs_patched.names == ["Input Device"]
    assert inputs_patched.ids == ["9999"]


def test_inputs_repr(inputs_patched) -> None:
    expected = """\
    MIDI Inputs (1)
    0:
        id: 9999
        name: Input Device
        manufacturer: DIY
        connection: open
        state: connected
    """
    assert repr(inputs_patched) == dedent(expected)


def test_input_properties(inputs_patched) -> None:
    midi = ipymidi.get_interface()
    input = inputs_patched[0]

    assert input.id == "9999"
    assert input.name == "Input Device"
    assert input.manufacturer == "DIY"
    assert input.connection == "open"
    assert input.state == "connected"

    # test updated state
    midi._inputs[0]["state"] = "disconnected"
    assert input.state == "disconnected"


@pytest.mark.parametrize("device_removed", [True, False])
def test_input_sync(inputs_patched, device_removed, monkeypatch: pytest.MonkeyPatch) -> None:
    midi = ipymidi.get_interface()
    input = inputs_patched[0]

    assert input.synced is True

    # update inputs (make `input` unsynced)
    if device_removed:
        new_inputs = []
    else:
        # another device
        new_inputs = deepcopy(midi._inputs)
        new_inputs[0]["id"] = "0000"
    monkeypatch.setattr(type(midi), "_inputs", new_inputs)

    assert input.synced is False

    # test unsynced input has frozen property values
    if not device_removed:
        midi._inputs[0]["state"] = "disconnected"

    assert input.id == "9999"
    assert input.state == "connected"


def test_input_repr(inputs_patched) -> None:
    expected = """\
    MIDI Input [0]
        id: 9999
        name: Input Device
        manufacturer: DIY
        connection: open
        state: connected
    """
    assert repr(inputs_patched[0]) == dedent(expected)
