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
# Create Gesture Recognizer
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
# Webcam
# -------------------------------
cap = cv2.VideoCapture(0)
timestamp = 0

last_gesture_time = 0
cooldown = 1.0  # seconds

def perform_action(gesture_name):
    global last_gesture_time
    current_time = time.time()

    if current_time - last_gesture_time < cooldown:
        return

    if gesture_name == "Open_Palm":
        pyautogui.press("f")
        print("f")

    elif gesture_name == "Thumb_Up":
        pyautogui.press("up")
        print("up")

    elif gesture_name == "Thumb_Down":
        pyautogui.press("down")
        print("down")

    elif gesture_name == "Victory":
        pyautogui.press("m")
        print("m")

    elif gesture_name == "Closed_Fist":
        pyautogui.press("k")
        print("k")

    elif gesture_name == "Pointing_Up":
        pyautogui.press("l")
        print("l")

    elif gesture_name == "ILoveYou":
        pyautogui.press("j")
        print("j")

    last_gesture_time = current_time


# -------------------------------
# CREATE FLOATING WINDOW
# -------------------------------
window_name = "YouTube Gesture Controller"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 400, 300)

# Get screen size
screen_width, screen_height = pyautogui.size()

# Position at top-right
x_position = screen_width - 410
y_position = 10
cv2.moveWindow(window_name, x_position, y_position)

# Make always on top
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
    result = gesture_recognizer.recognize_for_video(mp_image, timestamp)

    if result.hand_landmarks:
        for idx, hand_landmarks in enumerate(result.hand_landmarks):

            for lm in hand_landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

            for start_idx, end_idx in HAND_CONNECTIONS:
                x1 = int(hand_landmarks[start_idx].x * w)
                y1 = int(hand_landmarks[start_idx].y * h)
                x2 = int(hand_landmarks[end_idx].x * w)
                y2 = int(hand_landmarks[end_idx].y * h)
                cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

            if result.gestures and len(result.gestures[idx]) > 0:
                gesture = result.gestures[idx][0]
                gesture_name = gesture.category_name
                confidence = gesture.score

                perform_action(gesture_name)

                wrist = hand_landmarks[0]
                x = int(wrist.x * w)
                y = int(wrist.y * h)

                cv2.putText(
                    frame,
                    f"{gesture_name} ({confidence:.2f})",
                    (x - 20, y - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )

    # Resize frame to 400x300 for floating window
    small_frame = cv2.resize(frame, (400, 300))
    cv2.imshow(window_name, small_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
