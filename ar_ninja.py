"""
AR Gesture Control for Games (e.g., SEGA/Subway Surfers)
This script uses hand gestures mapped to keyboard inputs (Up, Down, Left, Right, Space)
based on five zones displayed on the webcam feed.

Dependencies: opencv-python, mediapipe, numpy, pyautogui.
"""

import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

# --- Configuration and State Variables ---
GAME_ACTIVE = False
START_TIMER_STARTED = 0
START_DELAY_SECONDS = 2 

# Initialize MediaPipe Hands and Drawing Utilities
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Initialize Video Capture (Webcam)
cap = cv2.VideoCapture(0)

# --- Helper Functions ---

def get_hand_center(landmarks, w, h):
    """Calculates the center pixel coordinate of the detected hand."""
    x_coords = [lm.x * w for lm in landmarks.landmark]
    y_coords = [lm.y * h for lm in landmarks.landmark]
    
    center_x = int(np.mean(x_coords))
    center_y = int(np.mean(y_coords))
    return center_x, center_y

def draw_zones(frame, hand_center_x, hand_center_y, w, h, active_zone=None):
    """Draws the 5-zone grid and highlights the active zone."""
    w_third = w // 3
    h_third = h // 3
    
    # Define colors and style
    LINE_COLOR = (200, 200, 200)
    HIGHLIGHT_COLOR = (0, 255, 255) 
    TEXT_COLOR = (255, 255, 255)
    THICKNESS = 3
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    
    # Draw vertical lines
    cv2.line(frame, (w_third, 0), (w_third, h), LINE_COLOR, THICKNESS)
    cv2.line(frame, (w * 2 // 3, 0), (w * 2 // 3, h), LINE_COLOR, THICKNESS)
    
    # Draw horizontal lines for Up/Down/Center (only within the central column)
    cv2.line(frame, (w_third, h_third), (w * 2 // 3, h_third), LINE_COLOR, THICKNESS) 
    cv2.line(frame, (w_third, h * 2 // 3), (w * 2 // 3, h * 2 // 3), LINE_COLOR, THICKNESS) 

    # Highlight the active zone and draw labels
    if active_zone == 'left':
        cv2.rectangle(frame, (0, 0), (w_third, h), HIGHLIGHT_COLOR, THICKNESS + 2)
        cv2.putText(frame, "LEFT", (w_third // 4, h // 2), FONT, 0.8, TEXT_COLOR, 2)
    elif active_zone == 'right':
        cv2.rectangle(frame, (w * 2 // 3, 0), (w, h), HIGHLIGHT_COLOR, THICKNESS + 2)
        cv2.putText(frame, "RIGHT", (w * 2 // 3 + w_third // 4, h // 2), FONT, 0.8, TEXT_COLOR, 2)
    elif active_zone == 'up':
        cv2.rectangle(frame, (w_third, 0), (w * 2 // 3, h_third), HIGHLIGHT_COLOR, THICKNESS + 2)
        cv2.putText(frame, "UP", (w_third + w_third // 4, h_third // 2), FONT, 0.8, TEXT_COLOR, 2)
    elif active_zone == 'down':
        cv2.rectangle(frame, (w_third, h * 2 // 3), (w * 2 // 3, h), HIGHLIGHT_COLOR, THICKNESS + 2)
        cv2.putText(frame, "DOWN", (w_third + w_third // 4, h * 2 // 3 + h_third // 2), FONT, 0.8, TEXT_COLOR, 2)
    elif active_zone == 'space': 
        cv2.rectangle(frame, (w_third, h_third), (w * 2 // 3, h * 2 // 3), HIGHLIGHT_COLOR, THICKNESS + 2)
        cv2.putText(frame, "CENTER/JUMP", (w_third + w_third // 6, h // 2), FONT, 0.7, TEXT_COLOR, 2)
    else: # Draw all labels if no zone is active
        cv2.putText(frame, "LEFT", (w_third // 4, h // 2), FONT, 0.8, TEXT_COLOR, 2)
        cv2.putText(frame, "RIGHT", (w * 2 // 3 + w_third // 4, h // 2), FONT, 0.8, TEXT_COLOR, 2)
        cv2.putText(frame, "UP", (w_third + w_third // 4, h_third // 2), FONT, 0.8, TEXT_COLOR, 2)
        cv2.putText(frame, "DOWN", (w_third + w_third // 4, h * 2 // 3 + h_third // 2), FONT, 0.8, TEXT_COLOR, 2)
        cv2.putText(frame, "CENTER/JUMP", (w_third + w_third // 6, h // 2), FONT, 0.7, TEXT_COLOR, 2)

    # Draw hand center point (the cursor)
    if hand_center_x != -1:
        cv2.circle(frame, (hand_center_x, hand_center_y), 10, (255, 0, 0), -1)

    return

# --- Main Logic Loop ---

while cap.isOpened():
    success, frame = cap.read()
    if not success: continue

    frame = cv2.flip(frame, 1) # Mirror image
    h, w, c = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    current_key_command = None
    hand_in_center = False
    
    # 4. Hand Detection and Command Mapping
    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        center_x, center_y = get_hand_center(hand_landmarks, w, h)
        
        # Draw hand landmarks for AR visual
        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                  mp_drawing_styles.get_default_hand_landmarks_style(),
                                  mp_drawing_styles.get_default_hand_connections_style())

        # Determine which zone the hand is in
        w_third = w // 3
        h_third = h // 3

        if center_x < w_third:
            current_key_command = 'left'
        elif center_x > w * 2 // 3:
            current_key_command = 'right'
        elif w_third <= center_x <= w * 2 // 3:
            if center_y < h_third:
                current_key_command = 'up'
            elif center_y > h * 2 // 3:
                current_key_command = 'down'
            else:
                current_key_command = 'space' # Center Zone for Jump/Start
                hand_in_center = True

    # 5. State Management and Visuals
    if not GAME_ACTIVE:
        # --- Beautiful Start Screen ---
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1) 
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0) # Darken background
        
        # Main Title
        cv2.putText(frame, "AR GESTURE GAME CONTROL", (w // 2 - 350, h // 4), 
                    cv2.FONT_HERSHEY_TRIPLEX, 1.5, (255, 255, 255), 3)

        # Instruction Text
        instruction_text = "PLACE HAND IN CENTER ZONE TO START"
        text_size, _ = cv2.getTextSize(instruction_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
        text_x = (w - text_size[0]) // 2
        text_y = h // 2
        cv2.putText(frame, instruction_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        # Draw Center Zone Guide
        w_third = w // 3
        h_third = h // 3
        cv2.rectangle(frame, (w_third, h_third), (w * 2 // 3, h * 2 // 3), (0, 255, 0) if hand_in_center else (0, 150, 0), 5)
        
        # Start Timer Logic
        if hand_in_center:
            if START_TIMER_STARTED == 0:
                START_TIMER_STARTED = time.time()
            elif time.time() - START_TIMER_STARTED > START_DELAY_SECONDS:
                GAME_ACTIVE = True
                START_TIMER_STARTED = 0
                time.sleep(1) 
        else:
            START_TIMER_STARTED = 0 

        if START_TIMER_STARTED > 0:
            remaining_time = int(START_DELAY_SECONDS - (time.time() - START_TIMER_STARTED)) + 1
            cv2.putText(frame, f"STARTING IN: {remaining_time}", (text_x, text_y + 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    else:
        # --- Gameplay Screen ---
        draw_zones(frame, center_x if results.multi_hand_landmarks else -1, 
                          center_y if results.multi_hand_landmarks else -1, 
                          w, h, active_zone=current_key_command)
        
        # Send keyboard command
        if current_key_command:
            pyautogui.press(current_key_command)
        
        # Display current action
        cv2.putText(frame, f"ACTION: {current_key_command if current_key_command else 'NONE'}", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)


    # Final display and Exit
    cv2.imshow('AR Gesture Game Control', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()