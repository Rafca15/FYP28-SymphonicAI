


let rawMidiEvents = [];

const audioContext = window.AudioContext ? new AudioContext() : new webkitAudioContext();

const sampleMidi = 60; 

function midi2rate(midi) {
    const interval = midi - sampleMidi;
    return Math.pow(2, interval / 12);
}

function scrollMiddleC() {
    window.scrollTo((keys.offsetWidth - document.body.offsetWidth) / 2, 0);
}

let I;



function requestMidi() {
    if (!('requestMIDIAccess' in navigator)) {
        msg.innerHTML = 'MIDI access not supported in this browser';
    } else {
        navigator.requestMIDIAccess().then(midi => {
            refresh(midi);
            midi.onstatechange = e => refresh(e.target);
        });
    }
}

function refresh(midi) {

    I = midi.inputs.size
        ? midi.inputs.values().next().value
        : void (0);

    msg.innerHTML = I
        ? 'Status: connected to ' + I.name
        : 'Status: not connected to a MIDI device'

    if (I) {
        I.onmidimessage = msg => {
            onMessage(msg);
        }
    }
}


const NOTEON = 144;
const NOTEOFF = 128;
const MAX_VELOCITY = 127;

const activeNotes = {};

function onMessage(msg) {
    const [type, note, velocity] = msg.data;
    const timestamp = performance.now();

    // Update key visuals
    const keyElement = document.getElementById('midi-' + note);
    if (keyElement) {
        if (type === NOTEON && velocity > 0) {
            keyElement.classList.add('activekey');
        } else if (type === NOTEOFF || (type === NOTEON && velocity === 0)) {
            keyElement.classList.remove('activekey');
        }
    }

    // Audio playback
    if (type === NOTEON && velocity > 0) {
        if (thereBeSound && !currentlyPlaying[note]) {
            currentlyPlaying[note] = playSample(midi2rate(note), velocity / 127);
        }
    } else if (type === NOTEOFF || (type === NOTEON && velocity === 0)) {
        if (currentlyPlaying[note]) {
            stop(currentlyPlaying[note]);
            delete currentlyPlaying[note];
        }
    }

    // Recording MIDI with durations
    if (isRecording) {
        const deltaTime = timestamp - recordingStartTime;

        // Convert to raw MIDI data bytes
        if (type === NOTEON || type === NOTEOFF) {
            const statusByte = type === NOTEON ? 0x90 : 0x80; // MIDI channel 0
            recordedMidiEvents.push({
                deltaTime: deltaTime,
                data: [statusByte, note, velocity]
            });
        }
    }
}

window.addEventListener('resize', () => {
    setTimeout(scrollMiddleC, 100);

});

let thereBeSound = false;
window.addEventListener('DOMContentLoaded', () => {
    setTimeout(scrollMiddleC, 100);

    // options: labels
    if (!localStorage.getItem('labels')) {
        localStorage.setItem('labels', true);
    }
    labels.checked = localStorage.getItem('labels') === 'true';
    if (labels.checked) {
        keys.classList.add('labels');
    }
    labels.onchange = () => {
        localStorage.setItem('labels', labels.checked);
        if (labels.checked) {
            keys.classList.add('labels');
            if (keylabels.checked) {
                keylabels.click();
            }
        } else {
            keys.classList.remove('labels');
        }
    };

    // options: keylabels
    if (!localStorage.getItem('keylabels')) {
        localStorage.setItem('keylabels', false);
    }
    keylabels.checked = localStorage.getItem('keylabels') === 'true';
    if (keylabels.checked) {
        keys.classList.add('keylabels');
    }
    keylabels.onchange = () => {
        localStorage.setItem('keylabels', keylabels.checked);
        if (keylabels.checked) {
            keys.classList.add('keylabels');
            if (labels.checked) {
                labels.click();
            }
        } else {
            keys.classList.remove('keylabels');
        }
    };

    // options: highlight color
    if (!localStorage.getItem('color')) {
        localStorage.setItem('color', '#FF7F50');
    }
    color.value = localStorage.getItem('color');
    document.styleSheets[0].cssRules[0].style.background = localStorage.getItem('color');
    color.onchange = function (e) {
        localStorage.setItem('color', e.target.value);
        document.styleSheets[0].cssRules[0].style.background = localStorage.getItem('color');
    };

    // options: play sounds
    if (!localStorage.getItem('sounds')) {
        localStorage.setItem('sounds', true);
    }
    sounds.checked = localStorage.getItem('sounds') === 'true';
    if (sounds.checked) {
        sounds.parentNode.getElementsByTagName('label')[0].className = 'soundon';
        thereBeSound = true;
    }
    sounds.onchange = () => {
        localStorage.setItem('sounds', sounds.checked);
        if (sounds.checked) {
            sounds.parentNode.getElementsByTagName('label')[0].className = 'soundon';
            thereBeSound = true;
        } else {
            sounds.parentNode.getElementsByTagName('label')[0].className = '';
            thereBeSound = false;
        }
    };

    showhideoptions.onclick = () => {
        opts.style.display = opts.style.display === 'inline-block' ? 'none' : 'inline-block';
    };

    requestMidi();

});

keys.onmousedown = keys.ontouchstart = keys.ondblclick = e => {
    onMessage({ data: [NOTEON, Number(e.target.id.replace('midi-', '')), MAX_VELOCITY] });
    e.target.classList.add('activekey');
};

keys.onmouseup = keys.ontouchend = e => {
    onMessage({ data: [NOTEOFF, Number(e.target.id.replace('midi-', '')), MAX_VELOCITY] });
    e.target.classList.remove('activekey');
};

const pressedKeys = new Set();

document.addEventListener('keydown', event => {
    const note = keysToMidi[event.key];
    if (note && !pressedKeys.has(event.key)) {
        pressedKeys.add(event.key);
        onMessage({ data: [NOTEON, note, MAX_VELOCITY] });
    }
});

document.addEventListener('keyup', event => {
    const note = keysToMidi[event.key];
    if (note && pressedKeys.has(event.key)) {
        pressedKeys.delete(event.key);
        onMessage({ data: [NOTEOFF, note, MAX_VELOCITY] });
    }
});



let sampleBuffer;

window.onload = function () {
    const arrayBuffer = new ArrayBuffer(sampleBase64.length);
    const len = sampleBase64.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = sampleBase64.charCodeAt(i);
    }
    audioContext.decodeAudioData(bytes.buffer, (buffer) => {
        sampleBuffer = buffer;
    });
};


const attackTime = 0.005;
const releaseTime = 0.1;



const currentlyPlaying = {};

function playNote(note, velocity) {
    if (currentlyPlaying[note]) stop(currentlyPlaying[note]);
    currentlyPlaying[note] = playSample(midi2rate(note), velocity / 127);
}

function stopNote(note) {
    if (currentlyPlaying[note]) {
        stop(currentlyPlaying[note]);
        delete currentlyPlaying[note];
    }
}

function playSample(rate, volume) {
    const sampleSource = audioContext.createBufferSource();
    sampleSource.buffer = sampleBuffer;
    sampleSource.playbackRate.value = rate;

    const gainNode = audioContext.createGain();
    gainNode.gain.value = volume;
    gainNode.gain.linearRampToValueAtTime(volume, audioContext.currentTime + attackTime);

    sampleSource.connect(gainNode);
    gainNode.connect(audioContext.destination);

    sampleSource.start();
    return gainNode;
}

function stop(gainNode) {
    gainNode.gain.setValueAtTime(gainNode.gain.value, audioContext.currentTime);
    gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + releaseTime);
}

const keysToMidi = {
    z: 48,
    s: 49,
    x: 50,
    d: 51,
    c: 52,
    v: 53,
    g: 54,
    b: 55,
    h: 56,
    n: 57,
    j: 58,
    m: 59,
    ',': 60,
    l: 61,
    '.': 62,
    q: 60,
    '2': 61,
    w: 62,
    '3': 63,
    e: 64,
    r: 65,
    '5': 66,
    t: 67,
    '6': 68,
    y: 69,
    '7': 70,
    u: 71,
    i: 72,
    '9': 73,
    o: 74,
    '0': 75,
    p: 76,
    '[': 77,
};


let isRecording = false;
let recordedMidiMessages = [];
let recordingStartTime = 0;

const recordBtn = document.getElementById('record-btn');

recordBtn.onclick = () => {
    toggleRecording();
};

document.addEventListener('keydown', event => {
    const note = keysToMidi[event.key];
    if (note && !pressedKeys.has(event.key)) {
        pressedKeys.add(event.key);
        onMessage({ data: [NOTEON, note, MAX_VELOCITY] });
    }
});

function generateMidiFile(events) {
    function writeVarLen(value) {
        const bytes = [];
        let buffer = value & 0x7F;
        while (value >>= 7) {
            buffer <<= 8;
            buffer |= ((value & 0x7F) | 0x80);
        }
        do {
            bytes.push(buffer & 0xFF);
            buffer >>= 8;
        } while (buffer);
        return bytes;
    }

    const header = [
        // Header Chunk
        0x4d, 0x54, 0x68, 0x64, // "MThd"
        0x00, 0x00, 0x00, 0x06, // header length
        0x00, 0x00,             // format type 0
        0x00, 0x01,             // one track
        0x01, 0xE0              // 480 ticks per quarter note (can change this)
    ];

    const track = [];
    let lastTimestamp = 0;

    events.forEach(e => {
        const delta = Math.round(e.deltaTime - lastTimestamp);
        lastTimestamp = e.deltaTime;
        const deltaBytes = writeVarLen(delta);
        track.push(...deltaBytes, ...e.data);
    });

    // End of track
    track.push(0x00, 0xFF, 0x2F, 0x00);

    const trackLength = track.length;
    const trackHeader = [
        0x4d, 0x54, 0x72, 0x6b,              // "MTrk"
        (trackLength >> 24) & 0xFF,
        (trackLength >> 16) & 0xFF,
        (trackLength >> 8) & 0xFF,
        trackLength & 0xFF
    ];

    const midiData = new Uint8Array([...header, ...trackHeader, ...track]);
    return new Blob([midiData], { type: 'audio/midi' });
}



function sendMidiToStreamlit(base64data) {
    const uniqueId = Math.random().toString(36).substring(7);
    console.log('Sending MIDI to backend...', base64data);

    fetch("http://localhost:9000", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: uniqueId, blob: base64data })
    }).then(res => {
        if (res.ok) {
            console.log("MIDI sent successfully.");
        } else {
            console.error("Failed to send MIDI.");
        }
    }).catch(err => console.error("Error:", err));
}


function toggleRecording() {
    isRecording = !isRecording;
    if (isRecording) {
        recordBtn.textContent = 'Send';
        recordBtn.classList.add('recording');
        recordedMidiEvents = [];
        recordingStartTime = performance.now();
        console.log('Recording started...');
    } else {
        recordBtn.textContent = 'Record';
        recordBtn.classList.remove('recording');
        console.log('Recording stopped. Generating MIDI file...');

        const midiBlob = generateMidiFile(recordedMidiEvents);

        const reader = new FileReader();
        reader.onload = function () {
            const base64data = reader.result.split(',')[1]; // Strip off "data:audio/midi;base64,"
            sendMidiToStreamlit(base64data);
        };
        reader.readAsDataURL(midiBlob);
    }
}



// // == Initialization ==
// const audioContext = window.AudioContext ? new AudioContext() : new webkitAudioContext();
// const NOTEON = 144, NOTEOFF = 128, MAX_VELOCITY = 127, sampleMidi = 60;
// const attackTime = 0.005, releaseTime = 0.1;
// const currentlyPlaying = {}, activeNotes = {};
// let sampleBuffer, isRecording = false, recordedMidiEvents = [], recordingStartTime = 0;
// let thereBeSound = false, I;

// // == Fake sample base64 (short dummy string for demonstration) ==
const sampleBase64 = atob("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");
