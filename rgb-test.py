import time
import os
import glob
import re
import atexit
import signal
import sys
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor

LOG_BASE = r"C:\ProgramData\Redshift\Log"

client = OpenRGBClient()

def set_breathing_red():
    for device in client.devices:
        for mode in device.modes:
            if mode.name.lower() == "breathing":
                mode.speed = 4
                mode.colors = [RGBColor(255, 0, 0)]
                device.set_mode(mode)

def set_solid_green():
    for device in client.devices:
        for mode in device.modes:
            if mode.name.lower() == "static":
                mode.colors = [RGBColor(0, 255, 0)]
                device.set_mode(mode)

def turn_off_lights():
    print("Cleaning up - turning off lights")
    try:
        for device in client.devices:
            device.set_color(RGBColor(0, 0, 0))
    except Exception as e:
        print(f"Cleanup error (safe to ignore): {e}")

def handle_exit(signum=None, frame=None):
    turn_off_lights()
    sys.exit(0)

# Register cleanup for normal exit, Ctrl+C, and termination signals
atexit.register(turn_off_lights)
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

def get_latest_log():
    folders = glob.glob(os.path.join(LOG_BASE, "Log.Latest.*"))
    if not folders:
        return None
    latest_folder = max(folders, key=os.path.getmtime)
    log_path = os.path.join(latest_folder, "log.html")
    if os.path.exists(log_path):
        return log_path
    return None

def get_recent_lines(path, num_lines=10):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        clean_lines = []
        for line in reversed(lines):
            clean = re.sub('<[^<]+?>', '', line).strip()
            if clean:
                clean_lines.append(clean)
            if len(clean_lines) >= num_lines:
                break
        return clean_lines
    except FileNotFoundError:
        return []

last_status = None

print("Watching Redshift log...")

try:
    while True:
        log_path = get_latest_log()
        if log_path:
            recent_lines = get_recent_lines(log_path, 10)
            recent_text = " ".join(recent_lines)

            if "Context: Unlocked:IPR" in recent_text or "Context: Unlocked:Render" in recent_text:
                if last_status != "finished":
                    print("Render finished - solid green")
                    set_solid_green()
                    last_status = "finished"
            else:
                if last_status != "rendering":
                    print("Rendering - breathing red")
                    set_breathing_red()
                    last_status = "rendering"

        time.sleep(1)
except Exception as e:
    print(f"Crashed: {e}")
    turn_off_lights()
    raise
