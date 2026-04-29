# OpenCV Pan-Tilt Laser Turret

A real-time computer vision targeting system built on an Arduino Mega 2560. A Python/OpenCV pipeline processes a live webcam feed to detect colored objects, computes the angular error from the frame center, and streams servo commands over serial to a pan-tilt bracket — all at 60fps with sub-100ms latency.

---

## How It Works

```
Webcam (60fps)
    │
    ▼
HSV Color Masking (OpenCV)
    │
    ▼
Contour Detection → Centroid Calculation
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

## Calibration

Physical misalignment between the camera and laser is corrected in software. Adjust these values at the top of `laser_tracker.py`:

```python
PAN_OFFSET  =    # degrees — positive shifts laser right
TILT_OFFSET =    # degrees — positive shifts laser up
```

Tune in increments of 5 until the laser dot lands on the tracked target.

---

## Tracking Modes

### Color Tracking ✅
Tracks a colored object using dual HSV range masking. Default target color is **red**, which requires two HSV ranges to cover both ends of the hue spectrum.

To track a different color, update the HSV bounds in `laser_tracker.py`:

Common presets:

| Color | Lower | Upper |
|-------|-------|-------|
| Green | `[40, 70, 70]` | `[80, 255, 255]` |
| Blue | `[100, 150, 50]` | `[130, 255, 255]` |
| Yellow | `[20, 100, 100]` | `[35, 255, 255]` |
