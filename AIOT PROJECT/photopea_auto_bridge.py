import argparse
import base64
import json
import mimetypes
import sys
import time
import urllib.parse
import webbrowser
from pathlib import Path

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("Missing dependency: pyserial")
    print("Install it with: pip install pyserial")
    sys.exit(1)

PRESET_SCRIPTS = {
    "brightshaky": """app.activeDocument.suspendHistory("Bright Shaky Preset","runPreset()");
function runPreset(){var doc=app.activeDocument;try{var id=stringIDToTypeID("brightnessEvent");var d=new ActionDescriptor();d.putInteger(charIDToTypeID("Brgh"),-3);d.putInteger(charIDToTypeID("Cntr"),10);executeAction(id,d,DialogModes.NO);}catch(e){}try{doc.activeLayer.applyUnSharpMask(85,1.0,0);}catch(e){}try{var dup=doc.activeLayer.duplicate();doc.activeLayer=dup;dup.applyHighPass(1.5);dup.blendMode=BlendMode.OVERLAY;dup.opacity=45;}catch(e){}}""",
    "brightstable": """app.activeDocument.suspendHistory("Bright Stable Preset","runPreset()");
function runPreset(){var doc=app.activeDocument;try{var id=stringIDToTypeID("brightnessEvent");var d=new ActionDescriptor();d.putInteger(charIDToTypeID("Brgh"),-5);d.putInteger(charIDToTypeID("Cntr"),12);executeAction(id,d,DialogModes.NO);}catch(e){}try{doc.activeLayer.applyUnSharpMask(30,1.0,0);}catch(e){}}""",
    "lowlightshaky": """app.activeDocument.suspendHistory("Lowlight Shaky Preset","runPreset()");
function runPreset(){var doc=app.activeDocument;try{var id=stringIDToTypeID("brightnessEvent");var d=new ActionDescriptor();d.putInteger(charIDToTypeID("Brgh"),22);d.putInteger(charIDToTypeID("Cntr"),5);executeAction(id,d,DialogModes.NO);}catch(e){}try{var id2=stringIDToTypeID("reduceNoise");var rn=new ActionDescriptor();rn.putInteger(stringIDToTypeID("strength"),7);rn.putInteger(stringIDToTypeID("preserveDetails"),30);rn.putInteger(stringIDToTypeID("reduceColorNoise"),55);rn.putInteger(stringIDToTypeID("sharpenDetails"),5);executeAction(id2,rn,DialogModes.NO);}catch(e){}try{doc.activeLayer.applyUnSharpMask(45,0.8,0);}catch(e){}try{var dup=doc.activeLayer.duplicate();doc.activeLayer=dup;dup.applyHighPass(1.0);dup.blendMode=BlendMode.SOFTLIGHT;dup.opacity=25;}catch(e){}}""",
    "lowlightstable": """app.activeDocument.suspendHistory("Lowlight Stable Preset","runPreset()");
function runPreset(){var doc=app.activeDocument;try{var id=stringIDToTypeID("brightnessEvent");var d=new ActionDescriptor();d.putInteger(charIDToTypeID("Brgh"),18);d.putInteger(charIDToTypeID("Cntr"),8);executeAction(id,d,DialogModes.NO);}catch(e){}try{var id2=stringIDToTypeID("reduceNoise");var rn=new ActionDescriptor();rn.putInteger(stringIDToTypeID("strength"),5);rn.putInteger(stringIDToTypeID("preserveDetails"),40);rn.putInteger(stringIDToTypeID("reduceColorNoise"),40);rn.putInteger(stringIDToTypeID("sharpenDetails"),10);executeAction(id2,rn,DialogModes.NO);}catch(e){}try{doc.activeLayer.applyUnSharpMask(25,0.8,0);}catch(e){}}""",
}

def image_to_data_uri(image_path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(image_path))
    if not mime:
        mime = "image/jpeg"
    data = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"

def build_photopea_url(image_path: Path, prediction: str) -> str:
    script = PRESET_SCRIPTS[prediction]
    cfg = {
        "files": [image_to_data_uri(image_path)],
        "environment": {
            "theme": 2,
            "panels": [2, 3, 11],  # Layers, Info, Actions
            "vmode": 0
        },
        "script": script
    }
    encoded = urllib.parse.quote(json.dumps(cfg, separators=(",", ":")))
    return f"https://www.photopea.com#{encoded}"

def infer_prediction(line: str) -> str | None:
    lower = line.strip().lower()
    markers = [
        "brightshaky",
        "brightstable",
        "lowlightshaky",
        "lowlightstable",
    ]
    for m in markers:
        if m in lower:
            return m
    return None

def list_ports():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports found.")
        return
    print("Available serial ports:")
    for p in ports:
        print(f"  {p.device} - {p.description}")

def main():
    parser = argparse.ArgumentParser(description="Bridge Arduino predictions to Photopea.")
    parser.add_argument("--port", required=False, help="Serial port, e.g. COM5 or /dev/tty.usbmodemXXXX")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--image", required=True, help="Path to local image file")
    parser.add_argument("--once", action="store_true", help="Open Photopea on first detected prediction and exit")
    parser.add_argument("--cooldown", type=float, default=3.0, help="Minimum seconds between launches")
    parser.add_argument("--list-ports", action="store_true", help="List available serial ports and exit")
    args = parser.parse_args()

    if args.list_ports:
        list_ports()
        return

    if not args.port:
        print("Please provide --port, or run with --list-ports first.")
        return

    image_path = Path(args.image).expanduser().resolve()
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        return

    ser = serial.Serial(args.port, args.baud, timeout=1)
    print(f"Listening on {args.port} @ {args.baud}")
    print(f"Using image: {image_path}")
    print("Waiting for predictions... Press Ctrl+C to stop.")

    last_launch_time = 0.0
    last_prediction = None

    try:
        while True:
            raw = ser.readline()
            if not raw:
                continue

            try:
                line = raw.decode("utf-8", errors="ignore").strip()
            except Exception:
                continue

            if not line:
                continue

            print(f"Serial: {line}")
            prediction = infer_prediction(line)
            if not prediction:
                continue

            now = time.time()
            if prediction == last_prediction and (now - last_launch_time) < args.cooldown:
                continue

            url = build_photopea_url(image_path, prediction)
            print(f"Opening Photopea with preset: {prediction}")
            webbrowser.open(url)

            last_prediction = prediction
            last_launch_time = now

            if args.once:
                break

    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
