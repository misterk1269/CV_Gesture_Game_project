import cv2
import mediapipe as mp
import pyautogui
import time

# --- Initialize MediaPipe ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5,
    model_complexity=0  # lightweight model for speed
)

# --- Webcam Setup ---
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # smaller frame = less lag
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# --- Variables ---
prev_x, prev_y = 0, 0
action = "NONE"
last_action_time = time.time()
COMMAND_COOLDOWN = 0.12  # 120ms between key presses
MOVE_THRESHOLD = 12       # sensitivity (lower = faster response)

while True:
    success, frame = cap.read()
    if not success:
        continue

    # Flip for mirror view and convert to RGB
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process frame
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        handLms = result.multi_hand_landmarks[0]

        # Get index fingertip (landmark 8)
        x = int(handLms.landmark[8].x * w)
        y = int(handLms.landmark[8].y * h)

        # Draw small circle on finger only (no landmarks)
        cv2.circle(frame, (x, y), 8, (0, 255, 0), -1)

        dx, dy = x - prev_x, y - prev_y

        # Detect motion direction
        if time.time() - last_action_time > COMMAND_COOLDOWN:
            if dx < -MOVE_THRESHOLD:
                pyautogui.press("left")
                action = "LEFT"
                last_action_time = time.time()
            elif dx > MOVE_THRESHOLD:
                pyautogui.press("right")
                action = "RIGHT"
                last_action_time = time.time()
            elif dy < -MOVE_THRESHOLD:
                pyautogui.press("up")
                action = "UP"
                last_action_time = time.time()
            elif dy > MOVE_THRESHOLD:
                pyautogui.press("down")
                action = "DOWN"
                last_action_time = time.time()
            else:
                action = "NONE"

        prev_x, prev_y = x, y

    # Display action text
    cv2.putText(frame, f"ACTION: {action}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Smooth Finger Control", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
