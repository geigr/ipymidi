import { AnyModel } from "@anywidget/types"
import { WebMidi, InputEventMap, MessageEvent, PortEvent, WebMidiEventMap } from "webmidi";
import type { IWidgetManager, WidgetModel } from "@jupyter-widgets/base";
import type { EventEmitter, Listener } from "webmidi";

// -- utils

async function loadModel(
    widget_manager: IWidgetManager,
    modelId: string,
): Promise<WidgetModel> {
    return await Promise.resolve(widget_manager.get_model(modelId.slice("IPY_MODEL_".length)));
}

// --- events

interface AddListenerArgs {
    target_type: 'webmidi' | 'input';
    target_id: string;
    event_model_id: string;
    event_name: string;
    event_props: string[];
    event_id: string;
}

interface RemoveListenerArgs {
    event_id: string;
}

const events = new Map<string, Listener | Listener[]>;

async function addListener(args: AddListenerArgs, manager: IWidgetManager) {
    let event_name: keyof InputEventMap | keyof WebMidiEventMap;
    let target: EventEmitter;

    if (args.target_type === "input") {
        event_name = args.event_name as keyof InputEventMap;
        target = WebMidi.getInputById(args.target_id);
    }
    else {
        // target_type === 'webmidi'
        event_name = args.event_name as keyof WebMidiEventMap;
        target = WebMidi;
    }

    loadModel(manager, args.event_model_id).then((event_model) => {
        const listener = target.addListener(event_name, (e: MessageEvent) => {
            console.log(e);
            event_model.set("value", e.value);
            event_model.save_changes();
        });

        events.set(args.event_id, listener);
    });

}

async function removeListener(args: RemoveListenerArgs) {
    const listeners = events.get(args.event_id);

    if (listeners === undefined) {
        return
    }

    if (Array.isArray(listeners)) {
        for (let ln of listeners) {
            ln.remove();
        }
    }
    else {
        listeners.remove();
    }

    events.delete(args.event_id);
}

// --- interface

interface InputProps {
    id: string;
    name: string;
    manufacturer: string;
    connection: string;
    state: string;
}

interface MIDIInterfaceModel {
    enabled: boolean;
	_inputs: InputProps[];
}

interface Command<T> {
    action: 'enable' | 'add_listener' | 'remove_listener';
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

export async function unstable_initialize({ model }: { model: AnyModel<MIDIInterfaceModel> }) {
    // clean-up: remove all WebMidi Listeners (should be safe as the MIDIInterface widget is a singleton)
    WebMidi.removeListener();
    events.clear();

    model.on("msg:custom", (command: Command<any>, _buffers: any) => {
        if (command.action === 'enable') {
		    WebMidi.enable().then(() => {
                model.set("enabled", true);
                updateInputs(model);
                model.save_changes();

                WebMidi.addListener("portschanged", (_: PortEvent) => {
                    updateInputs(model);
                    model.save_changes();
                });
            });
        }
        else if (command.action === 'add_listener') {
            addListener(command.args as AddListenerArgs, model.widget_manager);
        }
        else if (command.action === 'remove_listener') {
            removeListener(command.args as RemoveListenerArgs);
        }
    });
}

// TODO: basic render with
// - button for enabling the interface (+ enabled status indicator)
// - grid buttons for connecting / disconnecting input and output devices
