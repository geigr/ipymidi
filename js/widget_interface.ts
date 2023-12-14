import { AnyModel } from "@anywidget/types"
import { WebMidi, PortEvent } from "webmidi";


interface InputProps {
    id: string;
    name: string;
    manufacturer: string;
    connection: string;
    state: string;
}

export interface MIDIInterfaceModel {
    enabled: boolean;
	_inputs: InputProps[];
}

interface CustomMessage<T> {
    command: 'enable' | 'add_listener' | 'remove_listener';
    args?: T;
}

async function updateInputs(model: AnyModel<MIDIInterfaceModel>) {
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

export async function initialize_interface({ model }: { model: AnyModel<MIDIInterfaceModel> }) {
    // clean-up: remove all WebMidi Listeners (should be safe as the MIDIInterface widget is a singleton)
    WebMidi.removeListener();

    model.on("msg:custom", (msg: CustomMessage<any>, _buffers: any) => {
        switch (msg.command) {
            case 'enable':
		        WebMidi.enable().then(() => {
                    model.set("enabled", true);
                    updateInputs(model);
                    model.save_changes();

                    WebMidi.addListener("portschanged", (_: PortEvent) => {
                        updateInputs(model);
                        model.save_changes();
                    });
                });
                break;
            default:
                throw new Error('Unknown command ${msg.command}');
        }
    });
}

// TODO: basic render with
// - button for enabling the interface (+ enabled status indicator)
// - grid buttons for connecting / disconnecting input and output devices
