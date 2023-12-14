import traitlets as tt

EVENT_TRAITS: dict[str, dict[str, dict[str, tt.TraitType]]] = {
    "input": {
        "noteon": {
            "timestamp": tt.Int(help="Event trigger time (ms)"),
            "value": tt.Float(0.0, help="Attack velocity [0-1]"),
            "raw_value": tt.Int(0, help="Attack velocity [0-127]"),
        }
    }
}
