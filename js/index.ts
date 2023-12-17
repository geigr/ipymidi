import { initialize_listener } from './widget_event';
import { initialize_interface } from './widget_interface';

export async function unstable_initialize({ model }: { model: any }) {
    let widgetName = model.get('_anywidget_name');

    switch (widgetName) {
        case 'MIDIInterface':
            initialize_interface({ model });
            break;
        case 'Listener':
            initialize_listener({ model });
            break;
        default:
            throw new Error(`Unknown MIDI widget ${widgetName}`);
    }
}
