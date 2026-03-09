import math
import cv2
import mediapipe as mp
import pyautogui
import time
import win32gui
import win32con
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# -------------------------------
# MODEL PATH
# -------------------------------
MODEL_PATH = "models/gesture_recognizer.task"

# -------------------------------
# APP MODE
# -------------------------------
current_app = "youtube"
last_switch_time = 0
switch_cooldown = 2

# -------------------------------
# CUSTOM GESTURE LABELS
# -------------------------------
GESTURE_LABELS = {
    "Open_Palm": "Full Screen",
    "Thumb_Up": "Volume Up",
    "Thumb_Down": "Volume Down",
    "Victory": "Mute",
    "Closed_Fist": "Play / Pause",
    "Pointing_Up": "+10 Forward",
    "ILoveYou": "-10 Backward",
    "Point_Left": "Previous_Video",
    "Point_Right": "Next_Video",
    "None": "None"
}

# -------------------------------
# HAND CONNECTIONS
# -------------------------------
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17)
]

# -------------------------------
# CREATE GESTURE RECOGNIZER
# -------------------------------
BaseOptions = python.BaseOptions
GestureRecognizer = vision.GestureRecognizer
GestureRecognizerOptions = vision.GestureRecognizerOptions
VisionRunningMode = vision.RunningMode

options = GestureRecognizerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.VIDEO,
    num_hands=2
)

gesture_recognizer = GestureRecognizer.create_from_options(options)

# -------------------------------
# WEBCAM
# -------------------------------
cap = cv2.VideoCapture(0)
timestamp = 0

last_gesture_time = 0
cooldown = 1.0

# -------------------------------
# CUSTOM LANDMARK GESTURE
# -------------------------------
def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def detect_point_direction(hand_landmarks):

    base = hand_landmarks[5]
    tip = hand_landmarks[8]

    dx = tip.x - base.x
    dy = tip.y - base.y

    palm = hand_landmarks[9]

    # distances of other fingers from palm
    middle_dist = dist(hand_landmarks[12], palm)
    ring_dist   = dist(hand_landmarks[16], palm)
    pinky_dist  = dist(hand_landmarks[20], palm)

    # relaxed thresholds so thumb gestures don't interfere
    middle_folded = middle_dist < 0.20
    ring_folded   = ring_dist < 0.20
    pinky_folded  = pinky_dist < 0.20

    # thumb is intentionally ignored (floating)

    if not (middle_folded and ring_folded and pinky_folded):
        return None

    # detect horizontal pointing
    if abs(dx) > abs(dy):

        if dx > 0.08:   # slightly stronger threshold
            return "Point_Right"

        elif dx < -0.08:
            return "Point_Left"

    return None

# -------------------------------
# WINDOW ACTIVATION
# -------------------------------
def activate_window(title):

    hwnd = win32gui.FindWindow(None, title)

    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)

# -------------------------------
# SWITCH APPLICATION
# -------------------------------
def switch_app():

    global current_app, last_switch_time

    now = time.time()

    if now - last_switch_time < switch_cooldown:
        return

    if current_app == "youtube":
        current_app = "vlc"
        activate_window("VLC media player")
        print("Switched to VLC")

    else:
        current_app = "youtube"
        activate_window("YouTube")
        print("Switched to YouTube")

    last_switch_time = now


# -------------------------------
# PERFORM ACTION
# -------------------------------
def perform_action(gesture_name):

    global last_gesture_time

    now = time.time()

    if now - last_gesture_time < cooldown:
        return

    # YOUTUBE MODE
    if current_app == "youtube":

        if gesture_name == "Open_Palm":
            pyautogui.press("f")

        elif gesture_name == "Thumb_Up":
            pyautogui.press("up")

        elif gesture_name == "Thumb_Down":
            pyautogui.press("down")

        elif gesture_name == "Victory":
            pyautogui.press("m")

        elif gesture_name == "Closed_Fist":
            pyautogui.press("k")

        elif gesture_name == "Pointing_Up":
            pyautogui.press("l")

        elif gesture_name == "ILoveYou":
            pyautogui.press("j")

        elif gesture_name == "Point_Left":
            pyautogui.hotkey("shift","p")

        elif gesture_name == "Point_Right":
            pyautogui.hotkey("shift","n")

    # VLC MODE
    elif current_app == "vlc":

        if gesture_name == "Open_Palm":
            pyautogui.press("f")

        elif gesture_name == "Thumb_Up":
            pyautogui.press("up")

        elif gesture_name == "Thumb_Down":
            pyautogui.press("down")

        elif gesture_name == "Closed_Fist":
            pyautogui.press("space")

        elif gesture_name == "Pointing_Up":
            pyautogui.press("right")

        elif gesture_name == "ILoveYou":
            pyautogui.press("left")

        elif gesture_name == "Victory":
            pyautogui.press("m")

        elif gesture_name == "Point_Left":
            pyautogui.press("p")

        elif gesture_name == "Point_Right":
            pyautogui.press("n")

    last_gesture_time = now


# -------------------------------
# CREATE FLOATING WINDOW
# -------------------------------
window_name = "Gesture Controller"

cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

screen_width, screen_height = pyautogui.size()

x_position = screen_width - 410
y_position = 10

cv2.moveWindow(window_name, x_position, y_position)

hwnd = win32gui.FindWindow(None, window_name)

win32gui.SetWindowPos(
    hwnd,
    win32con.HWND_TOPMOST,
    x_position,
    y_position,
    400,
    300,
    0
)

# -------------------------------
# MAIN LOOP
# -------------------------------
while cap.isOpened():

    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    timestamp += 1

    result = gesture_recognizer.recognize_for_video(
        mp_image,
        timestamp
    )

    # -------------------------------
    # APP SWITCH GESTURE
    # -------------------------------
    if result.gestures and len(result.gestures) == 2:

        g1 = result.gestures[0][0].category_name
        g2 = result.gestures[1][0].category_name

        if g1 == "Pointing_Up" and g2 == "Pointing_Up":
            switch_app()

    # -------------------------------
    # DRAW HANDS
    # -------------------------------
    if result.hand_landmarks:

        for idx, hand_landmarks in enumerate(result.hand_landmarks):

            # Draw points
            for lm in hand_landmarks:

                cx = int(lm.x * w)
                cy = int(lm.y * h)

                cv2.circle(frame, (cx, cy), 5, (0,255,0), -1)

            # Draw connections
            for start, end in HAND_CONNECTIONS:

                x1 = int(hand_landmarks[start].x * w)
                y1 = int(hand_landmarks[start].y * h)

                x2 = int(hand_landmarks[end].x * w)
                y2 = int(hand_landmarks[end].y * h)

                cv2.line(frame,(x1,y1),(x2,y2),(255,0,0),2)

            # -------------------------------
            # GESTURE DETECTION
            # -------------------------------

            gesture_name = None
            confidence = 0

            # MODEL GESTURE FIRST
            if result.gestures and len(result.gestures[idx]) > 0:

                gesture = result.gestures[idx][0]

                if gesture.score > 0.6:
                    gesture_name = gesture.category_name
                    confidence = gesture.score

            # IF MODEL FAILS → CUSTOM
            if gesture_name is None:

                custom_gesture = detect_point_direction(hand_landmarks)

                if custom_gesture:
                    gesture_name = custom_gesture
                    confidence = 1.0

            # IF STILL NONE
            if gesture_name is None:
                gesture_name = "None"

            # PERFORM ACTION
            if gesture_name != "None":
                perform_action(gesture_name)

            # DISPLAY NAME
            display_name = GESTURE_LABELS.get(
                gesture_name,
                gesture_name
            )

            wrist = hand_landmarks[0]

            x = int(wrist.x * w)
            y = int(wrist.y * h)

            cv2.putText(
                frame,
                f"{display_name} ({confidence:.2f})",
                (x-20,y-20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0,0,255),
                2
            )

    # -------------------------------
    # SHOW CURRENT MODE
    # -------------------------------
    cv2.putText(
        frame,
        f"MODE: {current_app.upper()}",
        (10,30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0,255,255),
        2
    )

    small_frame = cv2.resize(frame,(400,300))

    cv2.imshow(window_name, small_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()