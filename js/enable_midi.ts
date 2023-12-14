// Copied and modified from https://github.com/jupyter-widgets/midicontrols
// Copyright (c) Project Jupyter Contributors
// Distributed under the terms of the Modified BSD License.

import { PromiseDelegate } from '@lumino/coreutils';
import { WebMidi } from 'webmidi';


export default async function enableMIDI() {
    if (WebMidi.enabled) {
        return;
    }

    const midiEnabled = new PromiseDelegate<void>();

    WebMidi
        .enable()
        .then(() => {
            midiEnabled.resolve(undefined);
        })
        .catch(err => midiEnabled.reject(err));

    await midiEnabled.promise;
}
