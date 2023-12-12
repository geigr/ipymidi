
import { AnyModel } from "@anywidget/types"

interface MidiEventModel {
}

export async function unstable_initialize({ model }: { model: AnyModel<MidiEventModel> }) {
    console.log(model);
}

// TODO: basic render with visual cue and trait values when the MIDI event is triggered
