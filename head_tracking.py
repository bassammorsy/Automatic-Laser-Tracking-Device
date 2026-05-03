import cv2
import serial
import time
import numpy as np
import os

# ── Config ───────────────────────────────────────────────────────
PORT = "/dev/cu.usbmodem11301"
BAUD = 115200

PAN_MIN,  PAN_MAX  = 0,   180
TILT_MIN, TILT_MAX = 20,  160
DEADZONE = 15
# ─────────────────────────────────────────────────────────────────

# ── Load calibration ─────────────────────────────────────────────
PAN_OFFSET  = 0
TILT_OFFSET = 0

cal_path = "/Users/bassammorsy/Desktop/calibration.txt"
if os.path.exists(cal_path):
    with open(cal_path) as f:
        for line in f:
            if line.startswith("PAN_OFFSET"):
                PAN_OFFSET = int(line.strip().split("=")[1])
            elif line.startswith("TILT_OFFSET"):
                TILT_OFFSET = int(line.strip().split("=")[1])
    print(f"Calibration loaded: PAN_OFFSET={PAN_OFFSET}  TILT_OFFSET={TILT_OFFSET}")
else:
    print("No calibration file — running with zero offsets")
# ─────────────────────────────────────────────────────────────────

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)
print("Connected. Press Q to quit.")

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

cap = cv2.VideoCapture(1)
if not cap.isOpened():
    print("ERROR: Camera not opened")
    exit()

cap.set(cv2.CAP_PROP_FPS,          60)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Camera: {actual_w}x{actual_h}")

pan_angle  = max(PAN_MIN,  min(PAN_MAX,  90 + PAN_OFFSET))
tilt_angle = max(TILT_MIN, min(TILT_MAX, 90 + TILT_OFFSET))

lost_time = None

def send(cmd):
    try:
        ser.write((cmd + '\n').encode())
    except Exception as e:
        print(f"Serial error: {e}")

send(f"P{pan_angle}")
send(f"T{tilt_angle}")
send("LON")
time.sleep(0.5)

while True:
    ret, frame = cap.read()
    if not ret:
        print("ERROR: Failed to read frame")
        break

    frame_h, frame_w = frame.shape[:2]
    cx, cy = frame_w // 2, frame_h // 2

    # Downscale for faster detection
    small   = cv2.resize(frame, (640, 360))
    gray    = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    scale_x = frame_w / 640
    scale_y = frame_h / 360

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=8,
        minSize=(80, 80)
    )

    if len(faces) > 0:
        lost_time = None  # reset lost timer

        largest = max(faces, key=lambda f: f[2] * f[3])
        (x, y, w, h) = largest

        # Scale back to full res
        x = int(x * scale_x)
        y = int(y * scale_y)
        w = int(w * scale_x)
        h = int(h * scale_y)

        head_x = x + w // 2
        head_y = y + h // 2

        # Chest is one face-height below head center
        chest_y = min(head_y + h, frame_h - 1)

        # Error from frame center
        error_x = head_x - cx
        error_y = chest_y - cy

        # Direct map — negative error_x so left/right is correct
        pan_angle  = 90 + PAN_OFFSET  - int(error_x / frame_w * 180)
        tilt_angle = 90 + TILT_OFFSET - int(error_y / frame_h * 140)
        pan_angle  = max(PAN_MIN,  min(PAN_MAX,  pan_angle))
        tilt_angle = max(TILT_MIN, min(TILT_MAX, tilt_angle))

        if abs(error_x) > DEADZONE:
            send(f"P{pan_angle}")
        if abs(error_y) > DEADZONE:
            send(f"T{tilt_angle}")

        print(f"Error: ({error_x},{error_y})  Pan: {pan_angle}  Tilt: {tilt_angle}")

        # Draw head box
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, "HEAD", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Draw chest aim dot
        cv2.circle(frame, (head_x, chest_y), 12, (0, 0, 255), -1)
        cv2.putText(frame, "CHEST AIM", (head_x + 15, chest_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    else:
        # Start lost timer if not already started
        if lost_time is None:
            lost_time = time.time()
        elif time.time() - lost_time > 1.5:
            send(f"P{90 + PAN_OFFSET}")
            send(f"T{90 + TILT_OFFSET}")

        cv2.putText(frame, "No face detected", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)
        print("No face detected")

    cv2.drawMarker(frame, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 40, 2)

    display = cv2.resize(frame, (1280, 720))
    cv2.imshow("Head Track / Chest Aim", display)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == ord('Q'):
        print("Quitting...")
        break

send("LOFF")
cap.release()
cv2.destroyAllWindows()
ser.close()