import cv2
import mediapipe as mp
import numpy as np
import re

# Initialize MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# OpenCV Video
cap = cv2.VideoCapture(0)

expression = ""
last_selected = ""
history = []  # Store expressions and results
history_scroll = 0  # Scroll offset

# Button layout (grid)
button_grid = [
    ["1", "2", "3", "+"],
    ["4", "5", "6", "-"],
    ["7", "8", "9", "*"],
    ["C", "0", "=", "/"],
    ["DEL", ".", "UP", "DOWN"]  # Added decimal and scroll buttons
]

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    overlay = frame.copy()

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    h, w, _ = frame.shape
    rows = len(button_grid)
    cols = max(len(row) for row in button_grid)
    button_w = int(w / (cols + 1))
    button_h = int(h / (rows + 2))

    buttons = []
    for row_idx, row in enumerate(button_grid):
        for col_idx, label in enumerate(row):
            x = (col_idx + 1) * button_w - int(button_w / 2)
            y = (row_idx + 1) * button_h + 50
            buttons.append({"label": label, "pos": (x, y)})

    # Draw translucent buttons with optional highlight
    for btn in buttons:
        x, y = btn["pos"]
        color = (255, 255, 255)
        if last_selected == btn["label"]:
            color = (0, 120, 255)
        cv2.rectangle(overlay, (x, y), (x + 80, y + 60), color, -1)
        cv2.putText(
            overlay, btn["label"], (x + 10, y + 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2
        )

    alpha = 0.4
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        landmarks = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]
        index_finger_tip = landmarks[8]
        middle_finger_tip = landmarks[12]

        cv2.circle(frame, index_finger_tip, 10, (0, 255, 255), cv2.FILLED)
        cv2.circle(frame, middle_finger_tip, 10, (255, 0, 255), cv2.FILLED)

        dist = np.linalg.norm(np.array(index_finger_tip) - np.array(middle_finger_tip))

        for btn in buttons:
            x, y = btn["pos"]
            if x < index_finger_tip[0] < x + 80 and y < index_finger_tip[1] < y + 60:
                cv2.rectangle(frame, (x, y), (x + 80, y + 60), (0, 255, 0), 3)

                if dist < 40 and last_selected != btn["label"]:
                    last_selected = btn["label"]
                    label = btn["label"]
                    if label == "C":
                        expression = ""
                    elif label == "DEL":
                        expression = expression[:-1]
                    elif label == "UP":
                        if history_scroll > 0:
                            history_scroll -= 1
                    elif label == "DOWN":
                        if history_scroll < max(0, len(history) - 2):
                            history_scroll += 1
                    elif label == "=":
                        try:
                            # Clean expression to remove leading zeros
                            safe_expr = re.sub(r'\b0+(\d+)', r'\1', expression)
                            result = str(eval(safe_expr))
                            history.append(f"{expression} = {result}")
                            expression = result
                            history_scroll = max(0, len(history) - 2)
                        except:
                            expression = "Error"
                    else:
                        expression += label

        if dist > 60:
            last_selected = ""

    # Show current expression
    cv2.putText(
        frame, expression, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3
    )

    # Display 2 items from scrollable history (max 5 stored)
    for i in range(2):
        if history_scroll + i < len(history):
            item = history[history_scroll + i]
            cv2.putText(
                frame, item, (50, 100 + i * 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 255, 100), 2
            )

    # Limit history size to 5
    if len(history) > 5:
        history = history[-5:]

    cv2.imshow("Virtual Calculator", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
