import traitlets as tt

MESSAGE = tt.Dict(
    per_key_traits={
        "type": tt.Unicode(help="message type"),
        "channel": tt.Int(min=1, max=16, allow_none=True, help="MIDI channel number"),
        "data": tt.List(
            tt.Int(min=0, max=255),
            help="MIDI message content as a list of bytes [0-255]",
        ),
    },
    help="Information about a single MIDI message",
)

TIMESTAMP = tt.Float(
    help="The moment when the event occurred [ms]",
    read_only=True,
)

NOTE_TRAITTYPES: dict[str, tt.TraitType] = {
    "note_accidental": tt.Unicode(allow_none=True, help="note name"),
    "note_attack": tt.Float(help="attack velocity [0-1]"),
    "note_duration": tt.Float(allow_none=True, help="duration the note should play for [ms]"),
    "note_identifier": tt.Unicode(help="full note identifier (name, accidental, octave)"),
    "note_name": tt.Unicode(help="note name"),
    "note_number": tt.Int(help="MIDI note number [0-127]"),
    "note_octave": tt.Int(help="note octave"),
    "note_raw_attack": tt.Int(help="attack velocity [0-127]"),
    "note_raw_release": tt.Int(help="release velocity [0-127]"),
    "note_release": tt.Float(help="release velocity [0-1]"),
}


EVENT_TRAITTYPES: dict[str, dict[str, dict[str, tt.TraitType]]] = {
    "interface": {
        "connected": {
            "timestamp": TIMESTAMP,
        },
        "disabled": {
            "timestamp": TIMESTAMP,
        },
        "disconnected": {
            "timestamp": TIMESTAMP,
        },
        "enabled": {
            "timestamp": TIMESTAMP,
        },
        "error": {
            "timestamp": TIMESTAMP,
        },
        "midiaccessgranted": {
            "timestamp": TIMESTAMP,
        },
        "portschanged": {
            "timestamp": TIMESTAMP,
        },
    },
    "input": {
        "midimessage": {
            "message": MESSAGE,
            "timestamp": TIMESTAMP,
        },
        "noteoff": dict(
            NOTE_TRAITTYPES,
            **{
                "value": tt.Float(0.0, help="Release velocity [0-1]"),
                "raw_value": tt.Int(0, help="Release velocity [0-127]"),
                "message": MESSAGE,
                "timestamp": TIMESTAMP,
            },
        ),
        "noteon": dict(
            NOTE_TRAITTYPES,
            **{
                "value": tt.Float(0.0, help="Attack velocity [0-1]"),
                "raw_value": tt.Int(0, help="Attack velocity [0-127]"),
                "message": MESSAGE,
                "timestamp": TIMESTAMP,
            },
        ),
    },
}
