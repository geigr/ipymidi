import { AnyModel } from "@anywidget/types"
import { WebMidi } from "webmidi";

interface InputProps {
    id: string;
    name: string;
    manufacturer: string;
    connection: string;
    state: string;
}

interface WebMidiModel {
    enabled: boolean;
	_inputs: InputProps[];
}

async function update_inputs(model: AnyModel<WebMidiModel>) {
    let inputs = new Array<InputProps>;
    WebMidi.inputs.forEach(device => {
        inputs.push({
            id: device.id,
            name: device.name,
            manufacturer: device.manufacturer,
            connection: device.connection,
            state: device.state
        });
    });
    model.set("_inputs", inputs);
}

export async function unstable_initialize({ model }: { model: AnyModel<WebMidiModel> }) {
    model.on("msg:custom", (command: any, _buffers: any) => {
        if (command.action === 'enable') {
		    WebMidi.enable().then(() => {
                model.set("enabled", true);
                update_inputs(model);
                model.save_changes();
            });
        }
    })
}
