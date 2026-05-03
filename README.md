# OpenCV Pan-Tilt Laser Turret
A real-time computer vision targeting system built on an Arduino Mega 2560. A Python/OpenCV pipeline processes a live webcam feed to detect colored objects or human faces, computes the angular error from the frame center, and streams servo commands over serial to a pan-tilt bracket — all at 60fps with sub-100ms latency.

---

## How It Works
```
Webcam (60fps / 1080p)
    │
    ▼
HSV Color Masking (OpenCV)  —or—  Haar Cascade Face Detection
    │
    ▼
Contour Detection → Centroid  —or—  Head centroid → Chest pixel estimate
    │
    ▼
Error Mapping → Servo Angles (0–180°)
    │
    ▼
Serial (115200 baud) → Arduino Mega
    │
    ▼
PWM → Pan Servo (D3) + Tilt Servo (D4) + Laser (D2)
```

The target's pixel position is mapped directly to a servo angle using a linear transform — no PID, no stepping — giving instant snap-to-target response. A configurable deadzone prevents jitter when the target is near center.

---

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Vision | Python 3, OpenCV, NumPy |
| Communication | PySerial at 115200 baud |
| Microcontroller | Arduino C++, Servo.h |
| Color Detection | HSV masking, contour detection |
| Face Detection | Haar Cascade classifier |
| Targeting | Centroid-to-angle linear mapping |

---

## Hardware

### Components
| Part | Details |
|------|---------|
| Arduino Mega 2560 | Microcontroller |
| SG90 Servo × 2 | Pan and tilt axes |
| KY-008 Laser Module | 5V, 650nm red dot |
| Pan/Tilt Bracket | Mechanical mount for both servos |
| Power Supply Module (PSM) | Dedicated 5V servo power |
| Breadboard + Jumper Wires | Prototyping |

### Wiring
| Component | Arduino Pin |
|-----------|-------------|
| Pan servo signal | D3 |
| Tilt servo signal | D4 |
| Laser signal | D2 |

**Power rail:**
- Servo VCC → PSM 5V output
- Servo GND → PSM GND → Arduino GND (shared ground — required)
- Laser VCC → Arduino 5V
- Arduino GND → Breadboard negative rail

> ⚠️ **Shared ground is critical.** Without it, the Arduino's PWM signal has no reference and the servos will behave erratically regardless of signal correctness.

---

## Serial Command Protocol
Commands are newline-terminated ASCII strings sent at 115200 baud.

| Command | Description | Example |
|---------|-------------|---------|
| `P<angle>` | Set pan servo | `P90` |
| `T<angle>` | Set tilt servo | `T45` |
| `LON` | Laser on | `LON` |
| `LOFF` | Laser off | `LOFF` |

Pan range: 0–180° — Tilt range: 20–160°

---

## Tracking Modes

### Color Tracking ✅
Tracks a colored object using dual HSV range masking. Default target color is **red**, which requires two HSV ranges to cover both ends of the hue spectrum.

To track a different color, update the HSV bounds in `laser_tracker.py`:

| Color | Lower | Upper |
|-------|-------|-------|
| Green | `[40, 70, 70]` | `[80, 255, 255]` |
| Blue | `[100, 150, 50]` | `[130, 255, 255]` |
| Yellow | `[20, 100, 100]` | `[35, 255, 255]` |

**Run:**
```bash
python3 laser_tracker.py
```

---

### Head Tracking ✅
Tracks a human face using OpenCV's Haar Cascade classifier and aims the laser at the **chest** — estimated as one face-height below the detected head center. This scales automatically with distance as the face gets larger or smaller in frame.

**How it works:**
```
Webcam (1080p)
    │
    ▼
Grayscale + Face Detection (Haar Cascade)
    │
    ▼
Head centroid → Chest pixel = head_y + face_height
    │
    ▼
Error from frame center → Servo angles
    │
    ▼
Serial → Arduino (pan on X error, tilt on Y error)
```

The laser targets the chest rather than the face by offsetting the tilt target one face-height downward from the detected head center. A deadzone prevents servo jitter when the target is near center.

**Run:**
```bash
python3 head_tracking.py
```

---

## Calibration

Physical misalignment between the camera and laser is corrected through a dedicated calibration script.

**Run calibration before tracking:**
```bash
python3 calibration.py
```

- A crosshair appears at the center of a **1080p** feed
- Use **arrow keys** to move the laser dot until it aligns with the crosshair
- Press **Enter** to save offsets to `calibration.txt`

`head_tracking.py` loads `calibration.txt` automatically on startup — no manual offset copying needed.

> ⚠️ Both scripts run at **1920×1080**. Calibration and tracking must use the same resolution or offsets won't transfer correctly.

For color tracking, offsets can also be set manually in `laser_tracker.py`:
```python
PAN_OFFSET  =    # degrees — positive shifts laser right
TILT_OFFSET =    # degrees — positive shifts laser up
```

Tune in increments of 5 until the laser dot lands on the tracked target.
