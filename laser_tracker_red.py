import cv2
import serial
import time
import numpy as np

# ── Config ───────────────────────────────────────────────────────
PORT = "/dev/cu.usbmodem11301"
BAUD = 115200

PAN_MIN,  PAN_MAX  = 0,   180
TILT_MIN, TILT_MAX = 20,  160
DEADZONE = 15

PAN_OFFSET  = 0
TILT_OFFSET = -23

LOWER_RED1 = np.array([0,   120,  70])
UPPER_RED1 = np.array([10,  255, 255])
LOWER_RED2 = np.array([170, 120,  70])
UPPER_RED2 = np.array([180, 255, 255])
# ─────────────────────────────────────────────────────────────────

ser = serial.Serial(PORT, BAUD, timeout=1)
print("Connected. Press Q in tracker window to quit.")
time.sleep(2)

cap = cv2.VideoCapture(1)
if not cap.isOpened():
    print("ERROR: Camera not opened")
    exit()

cap.set(cv2.CAP_PROP_FPS,          60)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
print(f"Camera FPS: {cap.get(cv2.CAP_PROP_FPS)}")

pan_angle  = 90
tilt_angle = 90

def send(cmd):
    try:
        ser.write((cmd + '\n').encode())
    except Exception as e:
        print(f"Serial error: {e}")

def map_to_angle(pixel, total_pixels, angle_min, angle_max, offset=0):
    ratio = pixel / total_pixels
    angle = int(angle_min + ratio * (angle_max - angle_min)) + offset
    return max(min(angle_min, angle_max), min(max(angle_min, angle_max), angle))

send("P90")
send("T90")
send("LON")
time.sleep(0.5)

while True:
    ret, frame = cap.read()
    if not ret:
        print("ERROR: Failed to read frame")
        break

    frame_h, frame_w = frame.shape[:2]
    cx, cy = frame_w // 2, frame_h // 2

    hsv   = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, LOWER_RED1, UPPER_RED1)
    mask2 = cv2.inRange(hsv, LOWER_RED2, UPPER_RED2)
    mask  = cv2.bitwise_or(mask1, mask2)
    mask  = cv2.erode(mask,  None, iterations=2)
    mask  = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest = max(contours, key=cv2.contourArea)
        area    = cv2.contourArea(largest)

        if area > 500:
            (x, y, w, h) = cv2.boundingRect(largest)
            target_x = x + w // 2
            target_y = y + h // 2

            error_x = target_x - cx
            error_y = target_y - cy

            new_pan  = map_to_angle(target_x, frame_w, PAN_MAX,  PAN_MIN,  PAN_OFFSET)
            new_tilt = map_to_angle(target_y, frame_h, TILT_MAX, TILT_MIN, TILT_OFFSET)

            if abs(error_x) > DEADZONE:
                pan_angle = new_pan
                print(f"Sending P{pan_angle}")
                send(f"P{pan_angle}")

            if abs(error_y) > DEADZONE:
                tilt_angle = new_tilt
                print(f"Sending T{tilt_angle}")
                send(f"T{tilt_angle}")

            print(f"Target: ({target_x},{target_y})  Error: ({error_x},{error_y})  Pan: {pan_angle}  Tilt: {tilt_angle}")

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.circle(frame, (target_x, target_y), 5, (0, 255, 0), -1)

    cv2.drawMarker(frame, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)

    mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    combined = np.hstack([frame, mask_rgb])
    cv2.imshow("Laser Tracker  |  Mask", combined)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == ord('Q'):
        print("Quitting...")
        break

send("LOFF")
cap.release()
cv2.destroyAllWindows()
ser.close()