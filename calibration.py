import cv2
import serial
import time
import numpy as np

# ── Config ───────────────────────────────────────────────────────
PORT = "/dev/cu.usbmodem11301"
BAUD = 115200

PAN_MIN,  PAN_MAX  = 0,   180
TILT_MIN, TILT_MAX = 20,  160
# ─────────────────────────────────────────────────────────────────

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)
print("Connected.")

cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def send(cmd):
    ser.write((cmd + '\n').encode())

pan_angle  = 90
tilt_angle = 90

send(f"P{pan_angle}")
send(f"T{tilt_angle}")
send("LON")
time.sleep(0.5)

print("\n=== LASER CALIBRATION ===")
print("Use arrow keys to move the laser to the center of the camera frame.")
print("Press ENTER to save calibration. Press Q to quit without saving.\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_h, frame_w = frame.shape[:2]
    cx, cy = frame_w // 2, frame_h // 2

    # Draw crosshair at frame center
    cv2.drawMarker(frame, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 40, 2)
    cv2.putText(frame, f"Pan: {pan_angle}  Tilt: {tilt_angle}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "Arrows to move | ENTER to save | Q to quit", (10, frame_h - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    cv2.imshow("Laser Calibration", frame)

    key = cv2.waitKey(30) & 0xFF

    moved = False

    if key == 81 or key == 2:    # left arrow
        pan_angle = min(PAN_MAX, pan_angle + 1)
        moved = True
    elif key == 83 or key == 3:  # right arrow
        pan_angle = max(PAN_MIN, pan_angle - 1)
        moved = True
    elif key == 82 or key == 0:  # up arrow
        tilt_angle = max(TILT_MIN, tilt_angle - 1)
        moved = True
    elif key == 84 or key == 1:  # down arrow
        tilt_angle = min(TILT_MAX, tilt_angle + 1)
        moved = True
    elif key == 13:              # ENTER — save
        with open("calibration.txt", "w") as f:
            f.write(f"PAN_OFFSET={pan_angle - 90}\n")
            f.write(f"TILT_OFFSET={tilt_angle - 90}\n")
        print(f"\n✅ Calibration saved!")
        print(f"   PAN_OFFSET  = {pan_angle - 90}")
        print(f"   TILT_OFFSET = {tilt_angle - 90}")
        print("\nAdd these values to the top of laser_tracker.py")
        break
    elif key == ord('q') or key == ord('Q'):
        print("Quit without saving.")
        break

    if moved:
        send(f"P{pan_angle}")
        send(f"T{tilt_angle}")
        time.sleep(0.05)

send("LOFF")
cap.release()
cv2.destroyAllWindows()
ser.close()