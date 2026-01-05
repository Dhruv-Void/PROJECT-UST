import pytesseract
from PIL import ImageGrab, ImageOps, ImageEnhance
import time, datetime, os, re, json
import win32gui

# -----------------------------
# PORTABLE PATH CONFIGURATION
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tesseract (portable) - assumes Tesseract is installed and added to PATH
pytesseract.pytesseract.tesseract_cmd = "tesseract"

# Screenshot folder (relative)
SAVE_DIR = os.path.join(BASE_DIR, "ocr_shots")
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# JSON folder (relative)
DATA_DIR = os.path.join(BASE_DIR, "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Create a new JSON file for each run
RUN_TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
JSON_FILE = os.path.join(DATA_DIR, "values_" + RUN_TIMESTAMP + ".json")

# -----------------------------
# CONFIG
# -----------------------------

SLEEP_TIME = 1
STRIKE_ALERT_LIMIT = 120
CPU_ALERT_LIMIT = 80

# -----------------------------
# LOGGING
# -----------------------------

def log(msg):
    ts = "[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
    print(ts + msg)

# -----------------------------
# WINDOW DETECTION
# -----------------------------

def is_window_open(title):
    def callback(hwnd, found):
        if title.lower() in win32gui.GetWindowText(hwnd).lower():
            found.append(True)
        return True

    found = []
    win32gui.EnumWindows(callback, found)
    return bool(found)

# -----------------------------
# IMAGE PREPROCESSING
# -----------------------------

def preprocess(img):
    gray = ImageOps.grayscale(img)
    enhancer = ImageEnhance.Contrast(gray)
    gray = enhancer.enhance(2.0)
    gray = gray.resize((gray.size[0] * 2, gray.size[1] * 2))
    bw = gray.point(lambda x: 0 if x < 180 else 255)
    return bw

# -----------------------------
# OCR VALUE EXTRACTION
# -----------------------------

def extract_values(text):
    strike = None
    cpu = None

    m1 = re.search(r"strike\s*rate[^0-9]*([0-9]{1,3})", text, flags=re.IGNORECASE)
    if m1:
        val = int(m1.group(1))
        if 1 <= val <= 150:
            strike = val

    m2 = re.search(r"cpu\s*usage[^0-9]*([0-9]{1,3})", text, flags=re.IGNORECASE)
    if m2:
        val = int(m2.group(1))
        if 1 <= val <= 100:
            cpu = val

    return strike, cpu

# -----------------------------
# JSON SAVE
# -----------------------------

def save_json(strike, cpu):
    entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "strike_rate": strike,
        "cpu_usage": cpu
    }

    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r") as f:
                data = json.load(f)
        except:
            data = []
    else:
        data = []

    data.append(entry)

    with open(JSON_FILE, "w") as f:
        json.dump(data, f, indent=4)

# -----------------------------
# SCREENSHOT SAVE
# -----------------------------

def save_screenshot(img, reason):
    filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + reason + ".png"
    path = os.path.join(SAVE_DIR, filename)
    img.save(path)
    log("Screenshot saved: " + path)

# -----------------------------
# MAIN LOOP
# -----------------------------

def main():
    log("=== OCR Started (Window Aware) ===")

    last_strike = None
    last_cpu = None
    strike_alerted = False
    cpu_alerted = False

    while True:

        if not is_window_open("OCR Demo"):
            log("HTML window not open - skipping OCR")
            time.sleep(1)
            continue

        img = ImageGrab.grab()
        bw = preprocess(img)

        try:
            text = pytesseract.image_to_string(bw, config="--psm 6")
        except Exception as e:
            log("OCR error: " + str(e))
            time.sleep(SLEEP_TIME)
            continue

        clean = text.encode("ascii", "ignore").decode("ascii")
        strike, cpu = extract_values(clean)

        if strike is not None and cpu is not None:
            save_json(strike, cpu)

        # STRIKE RATE LOGIC
        if strike is not None:
            if strike != last_strike:
                log("Strike Rate Detected: " + str(strike))
                save_screenshot(img, "strike")
                last_strike = strike

            if strike > STRIKE_ALERT_LIMIT and not strike_alerted:
                log("WARNING: Strike Rate too high (" + str(strike) + ")")
                save_screenshot(img, "SR_ALERT")
                strike_alerted = True

            if strike <= STRIKE_ALERT_LIMIT:
                strike_alerted = False
        else:
            log("Strike Rate not detected")

        # CPU LOGIC
        if cpu is not None:
            if cpu != last_cpu:
                log("CPU Usage Detected: " + str(cpu))
                save_screenshot(img, "cpu")
                last_cpu = cpu

            if cpu > CPU_ALERT_LIMIT and not cpu_alerted:
                log("WARNING: CPU Usage too high (" + str(cpu) + ")")
                save_screenshot(img, "CPU_ALERT")
                cpu_alerted = True

            if cpu <= CPU_ALERT_LIMIT:
                cpu_alerted = False
        else:
            log("CPU Usage not detected")

        time.sleep(SLEEP_TIME)

# -----------------------------
# ENTRY POINT
# -----------------------------

if __name__ == "__main__":
    main()
