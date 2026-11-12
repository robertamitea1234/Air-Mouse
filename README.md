# Air Gesture Control

Control your computer with hand gestures using just a webcam. The script tracks your hand with MediaPipe and turns gestures into mouse movement and keyboard actions via PyAutoGUI.

## Features

| Gesture | Action |
|---|---|
| Move your index finger | Moves the mouse cursor (smoothed) |
| Hold still for 3 seconds | Locks the cursor for 5 seconds |
| Make a fist | Presses `Space` (once per fist) and pauses cursor movement |
| Swipe an open palm downward | Minimizes all windows (`Win + M`) |

A live camera preview shows the detected hand landmarks and the current status (`LIBER`, `NEMISCAT x/3s`, `BLOCAT`).

> **Pinch-to-click** (thumb + index finger while the cursor is locked) is implemented but currently commented out in the code. Uncomment the "Click" block to enable it.

## Requirements

- Python 3.8+
- A webcam
- **Windows** (the swipe gesture uses `Win + M`; everything else works cross-platform, but you would need to change that hotkey on macOS/Linux)

Python packages:

```
opencv-python
mediapipe
pyautogui
numpy
```

## Installation

```bash
git clone <https://github.com/robertamitea1234/Air-Mouse>
cd <your-repo-folder>
pip install opencv-python mediapipe pyautogui numpy
```

## Usage

```bash
python air_mouse.py
```

- Show one hand to the camera. The image is mirrored, so moving your hand right moves the cursor right.
- Press **Esc** in the preview window to quit.

## Configuration

All settings are at the top of `air_mouse.py`:

| Setting | Default | Description |
|---|---|---|
| `STILL_TIME` | `3.0` | Seconds of staying still before the cursor locks |
| `LOCK_TIME` | `5.0` | Seconds the cursor stays locked |
| `STILL_RADIUS` | `40` | Screen pixels the cursor may drift and still count as "still" |
| `PINCH_DIST` | `35` | Camera pixels between thumb and index tip to count as a pinch |
| `CLICK_COOLDOWN` | `0.5` | Minimum seconds between clicks |
| `FIST_COOLDOWN` | `1.0` | Minimum seconds between `Space` presses |
| `SWIPE_COOLDOWN` | `2.0` | Minimum seconds between swipes |
| `SWIPE_WINDOW` | `1` | Time window (seconds) in which the downward swipe must happen |
| `SWIPE_MIN_DY` | `0.25` | Fraction of image height the palm must travel down |
| `SMOOTHING` | `0.1` | Cursor smoothing, 0–1 (lower = smoother but slower) |
| `MARGIN` | `100` | Camera border (pixels) ignored, so you can reach screen edges comfortably |

## How it works

1. Each frame is read from the webcam, flipped horizontally and passed to MediaPipe Hands (one hand max).
2. A finger counts as extended if its tip is farther from the wrist than its PIP joint. No fingers extended = fist; all four extended = open palm.
3. The index fingertip position is mapped from the camera area (minus `MARGIN`) to screen coordinates and smoothed before moving the cursor.
4. The palm center is tracked over the last `SWIPE_WINDOW` seconds to detect a mostly-vertical downward swipe.

## Notes

- `pyautogui.FAILSAFE` is disabled, so moving the mouse to a screen corner will **not** abort the script. Use Esc in the preview window to exit.
- Good, even lighting and a plain background improve hand detection.
- The code comments are in Romanian.
