
import { AnyModel } from "@anywidget/types";
import { WebMidi, InputEventMap, MessageEvent, WebMidiEventMap } from "webmidi";
import type { EventEmitter } from "webmidi";

type ObjectHash = Record<string, any>;

interface MIDIEventModel extends ObjectHash {
    _id: string;
    _target_id: string | null;
    _target_type: 'webmidi' | 'input';
    _name: string;
    _prop_names: string[];
    enabled: boolean;
}

export async function unstable_initialize({ model }: { model: AnyModel<MIDIEventModel> }) {
    WebMidi.enable().then(() => {
        const target_type = model.get("_target_type");

        let event_name: keyof InputEventMap | keyof WebMidiEventMap;
        let target: EventEmitter;

        if (target_type === "input") {
            event_name = model.get('_name') as keyof InputEventMap;
            const target_id = model.get('_target_id') as string;
            target = WebMidi.getInputById(target_id);
        }
        else {
            // target_type === 'webmidi'
            event_name = model.get('_name') as keyof WebMidiEventMap;
            target = WebMidi;
        }

        target.addListener(event_name, (e: MessageEvent) => {
            console.log(e);
            // TODO: use model.get('_prop_names');
            model.set("value", e.value);
            model.save_changes();
        });
    });
}

// TODO: basic render with visual cue and trait values when the MIDI event is triggered
