import time
from collections import deque

import cv2
import mediapipe as mp
import pyautogui
import numpy as np

# ---------------- SETARI (le poti modifica) ----------------
STILL_TIME = 3.0        # secunde nemiscat pana se blocheaza cursorul
LOCK_TIME = 5.0         # secunde cat ramane blocat
STILL_RADIUS = 40       # pixeli ecran: cat se poate misca si tot conteaza "nemiscat"
PINCH_DIST = 35         # pixeli camera: distanta deget mare - aratator pentru click
CLICK_COOLDOWN = 0.5    # pauza minima intre doua click-uri
FIST_COOLDOWN = 1.0     # pauza minima intre doua apasari de space
SWIPE_COOLDOWN = 2.0    # pauza minima intre doua swipe-uri
SWIPE_WINDOW = 1      # secunde: in cat timp trebuie facuta miscarea in jos
SWIPE_MIN_DY = 0.25     # cat din inaltimea imaginii trebuie sa coboare mana (0.25 = 25%)
SMOOTHING = 0.1        # 0..1, mai mic = cursor mai fin dar mai lent
MARGIN = 100            # margine ignorata in camera (pixeli)
# -----------------------------------------------------------

cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

screen_width, screen_height = pyautogui.size()
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# (varf deget, articulatia PIP) pentru aratator, mijlociu, inelar, mic
FINGERS = [(8, 6), (12, 10), (16, 14), (20, 18)]


def dist(a, b):
    return np.hypot(a.x - b.x, a.y - b.y)


def fingers_extended(lm):
    """Lista de 4 valori True/False: True = deget intins."""
    wrist = lm[0]
    return [dist(wrist, lm[tip]) > dist(wrist, lm[pip]) for tip, pip in FINGERS]


# Stare
locked = False
lock_until = 0.0
anchor = None           # pozitia de referinta pentru "nemiscat"
still_start = 0.0
smooth_x = smooth_y = None

was_pinching = False
was_fist = False
last_click = last_fist = last_swipe = 0.0
palm_history = deque()  # (timp, x, y) pentru detectarea swipe-ului

while cap.isOpened():
    success, image = cap.read()
    if not success:
        break

    image = cv2.flip(image, 1)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_image)
    h, w, _ = image.shape
    now = time.time()

    # Deblocare cand expira timpul
    if locked and now >= lock_until:
        locked = False
        anchor = None

    status = "LIBER"

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            lm = hand_landmarks.landmark

            index_tip = lm[8]
            thumb_tip = lm[4]

            extended = fingers_extended(lm)
            is_fist = not any(extended)
            is_open_palm = all(extended)

            # ---------- Pumn -> SPACE (o data per pumn) ----------
            if is_fist and not was_fist and now - last_fist > FIST_COOLDOWN:
                pyautogui.press("space")
                last_fist = now
                print("Pumn -> space")
            was_fist = is_fist

            # ---------- Swipe in jos (palma deschisa) -> minimizeaza tot ----------
            palm = lm[9]  # centrul palmei
            palm_history.append((now, palm.x, palm.y))
            while palm_history and now - palm_history[0][0] > SWIPE_WINDOW:
                palm_history.popleft()

            if is_open_palm and now - last_swipe > SWIPE_COOLDOWN and len(palm_history) > 3:
                _, x0, y0 = palm_history[0]
                dy = palm.y - y0
                dx = abs(palm.x - x0)
                if dy > SWIPE_MIN_DY and dx < dy:
                    pyautogui.hotkey("win", "m")  # minimizeaza toate ferestrele in bara
                    last_swipe = now
                    palm_history.clear()
                    print("Swipe in jos -> minimizeaza tot")

            # ---------- Cursor ----------
            # Cand faci pumn cursorul nu se misca
            if not is_fist and not locked:
                target_x = np.interp(index_tip.x * w, (MARGIN, w - MARGIN), (0, screen_width))
                target_y = np.interp(index_tip.y * h, (MARGIN, h - MARGIN), (0, screen_height))

                if smooth_x is None:
                    smooth_x, smooth_y = target_x, target_y
                else:
                    smooth_x += (target_x - smooth_x) * SMOOTHING
                    smooth_y += (target_y - smooth_y) * SMOOTHING

                pyautogui.moveTo(smooth_x, smooth_y)

                # Detectare "nemiscat"
                pos = np.array([smooth_x, smooth_y])
                if anchor is None or np.linalg.norm(pos - anchor) > STILL_RADIUS:
                    anchor = pos
                    still_start = now
                elif now - still_start >= STILL_TIME:
                    locked = True
                    lock_until = now + LOCK_TIME
                    print("Cursor blocat")
                status = f"NEMISCAT {min(now - still_start, STILL_TIME):.1f}/{STILL_TIME:.0f}s"
            elif is_fist:
                anchor = None  # pumnul reseteaza numaratoarea

            # ---------- Click (DOAR cand cursorul e blocat) ----------
            # distance = np.hypot((index_tip.x - thumb_tip.x) * w, (index_tip.y - thumb_tip.y) * h)
            # pinching = distance < PINCH_DIST

            # if locked:
            #     status = f"BLOCAT {max(0, lock_until - now):.1f}s - ciupeste pentru click"
            #     if pinching and not was_pinching and now - last_click > CLICK_COOLDOWN:
            #         pyautogui.click()
            #         last_click = now
            #         print("Click")
            # was_pinching = pinching
    else:
        # Nicio mana detectata
        anchor = None
        smooth_x = smooth_y = None
        was_pinching = False
        was_fist = False
        palm_history.clear()
        if locked:
            status = f"BLOCAT {max(0, lock_until - now):.1f}s"

    color = (0, 0, 255) if locked else (0, 255, 0)
    cv2.putText(image, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow("Air Gesture Control", image)
    if cv2.waitKey(1) & 0xFF == 27:  # Esc pentru iesire
        break

cap.release()
cv2.destroyAllWindows()