import { AnyModel } from '@anywidget/types';
import { WebMidi, InputEventMap, Event, WebMidiEventMap } from 'webmidi';
import type { EventEmitter } from 'webmidi';
import enableMIDI from './enable_midi';

function toCamelCase(str: string): string {
    return str.replace(/_([a-z])/g, (_, p1) => p1.toUpperCase());
}

type ObjectHash = Record<string, any>;

export interface MIDIEventModel extends ObjectHash {
    _target_id: string | null;
    _target_type: 'webmidi' | 'input';
    _name: string;
    _prop_names: string[];
    enabled: boolean;
    count: number;
    timestamp: number;
}

export async function initialize_event({
    model,
}: {
    model: AnyModel<MIDIEventModel>;
}) {
    await enableMIDI();

    const prop_names = model.get('_prop_names');
    const prop_names_js = prop_names.map((pn) => {
        return toCamelCase(pn);
    });

    const callback = (e: Event) => {
        console.log(e);
        prop_names.forEach((pn, i) => {
            model.set(pn, (e as any)[prop_names_js[i]]);
        });
        model.set('count', model.get('count') + 1);
        model.set('timestamp', e.timestamp);
        model.save_changes();
    };

    const target_type = model.get('_target_type');

    let event_name: keyof InputEventMap | keyof WebMidiEventMap;
    let target: EventEmitter;

    if (target_type === 'input') {
        event_name = model.get('_name') as keyof InputEventMap;
        const target_id = model.get('_target_id') as string;
        target = WebMidi.getInputById(target_id);
    } else {
        // target_type === 'webmidi'
        event_name = model.get('_name') as keyof WebMidiEventMap;
        target = WebMidi;
    }

    // cleanup (HMR)
    target.removeListener(event_name, callback);

    target.addListener(event_name, callback);

    model.on('change:enabled', () => {
        if (model.get('enabled')) {
            if (!target.hasListener(event_name, callback)) {
                target.addListener(event_name, callback);
            }
        } else {
            target.removeListener(event_name, callback);
        }
    });

    // TODO: use model.once when it is exposed in AnyWidget's interface
    // https://github.com/manzt/anywidget/issues/402
    model.on('destroy', () => {
        target.removeListener(event_name, callback);
    });
}

// TODO: basic render with visual cue and trait values when the MIDI event is triggered
