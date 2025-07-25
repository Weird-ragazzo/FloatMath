import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import re

# MediaPipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

# App state
expression = ""
history = []
history_scroll = 0
last_selected = ""
theme = "light"

# Button layout
grid_layout = [
    ["1", "2", "3", "+"],
    ["4", "5", "6", "-"],
    ["7", "8", "9", "*"],
    ["C", "0", "=", "/"],
    ["DEL", ".", "^", "v"]
]

# Fonts
modern_fonts = {
    "heading": ("Segoe UI", 28, "bold"),
    "label": ("Segoe UI", 18, "bold"),
    "text": ("Consolas", 16),
    "button": ("Segoe UI", 12, "bold"),
    "footer": ("Segoe UI", 11, "italic")
}

# Colors
colors = {
    "light": {"bg": "#f9f9fb", "fg": "#1e1e1e", "entry_bg": "#ffffff", "hover": (255, 245, 180), "glow": (255, 220, 120)},
    "dark": {"bg": "#1e1e1e", "fg": "#f9f9f9", "entry_bg": "#2c2c2c", "hover": (150, 150, 150), "glow": (200, 200, 200)}
}

# Theme toggle function
def toggle_theme():
    global theme
    theme = "dark" if theme == "light" else "light"
    style_ui()

# Apply theme to UI elements
def style_ui():
    c = colors[theme]
    border_color = '#cccccc' if theme == 'light' else '#444444'
    root.configure(bg=c["bg"])
    frame_video.configure(bg=c["bg"])
    frame_controls.configure(bg=c["bg"], highlightbackground=border_color, highlightthickness=1)
    label_expr.configure(bg=c["entry_bg"], fg=c["fg"], relief="solid", bd=2, highlightbackground=border_color, highlightcolor=border_color)
    label_history.configure(bg=c["bg"], fg=c["fg"])
    listbox_history.configure(bg=c["entry_bg"], fg=c["fg"], relief="solid", bd=2, highlightbackground=border_color, highlightcolor=border_color)
    label_footer.configure(bg=c["bg"], fg=c["fg"])
    theme_button.configure(bg=c["entry_bg"], fg=c["fg"], relief="flat", bd=0)

# Initialize GUI


root = tk.Tk()


root.title("FloatMath")
root.geometry("1100x700")

frame_video = tk.Label(root)
frame_video.pack(side=tk.LEFT, padx=20, pady=20)

frame_controls = tk.Frame(root)
frame_controls.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)

label_expr = tk.Label(frame_controls, text="", font=modern_fonts["heading"], anchor="w", relief="solid", bd=2, highlightthickness=1, highlightbackground="#999", bg="#ffffff")
label_expr.pack(fill=tk.X, pady=(0, 20), ipady=10)

label_history = tk.Label(frame_controls, text="History", font=modern_fonts["label"], anchor="w")
label_history.pack(fill=tk.X)

listbox_history = tk.Listbox(frame_controls, height=3, font=modern_fonts["text"], activestyle='none', relief="solid", bd=2, highlightthickness=1, highlightbackground="#999", bg="#ffffff")
listbox_history.pack(fill=tk.X, pady=(0, 20))

theme_button = tk.Button(frame_controls, text="Toggle Theme", font=modern_fonts["button"], command=toggle_theme, relief="raised", bd=2, bg="#4CAF50", fg="white", activebackground="#45a049", highlightthickness=0, cursor="hand2")
theme_button.pack(pady=(0, 5))

label_thanks = tk.Label(frame_controls, text="Thanks for using FloatMath!", font=("Segoe UI", 12), anchor="center")
label_thanks.pack(pady=(0, 15))

label_footer = tk.Label(root, text="© 2025 Made by Dhruv Raghav", font=modern_fonts["footer"], bg=colors[theme]["bg"], fg=colors[theme]["fg"])
label_footer.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 10))

# Apply initial theme
style_ui()

# OpenCV
cap = cv2.VideoCapture(0)

# GUI update loop
def update_frame():
    global expression, history, history_scroll, last_selected
    ret, frame = cap.read()
    if not ret:
        root.after(10, update_frame)
        return
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    h, w, _ = frame.shape

    # Draw buttons
    buttons = []
    total_rows = len(grid_layout)
    hover = colors[theme]["hover"]
    glow = colors[theme]["glow"]

    for row_idx, row in enumerate(grid_layout):
        for col_idx, label in enumerate(row):
            x = (col_idx + 1) * int(w / 6)
            y = (row_idx + 1) * int(h / (total_rows + 2))
            buttons.append({"label": label, "pos": (x, y)})
            cv2.rectangle(frame, (x, y), (x + 80, y + 60), hover, -1, lineType=cv2.LINE_AA)
            cv2.putText(frame, label, (x + 15, y + 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 50, 50), 2)

    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        h_points = hand_landmarks.landmark
        index_tip = int(h_points[8].x * w), int(h_points[8].y * h)
        middle_tip = int(h_points[12].x * w), int(h_points[12].y * h)

        cv2.circle(frame, index_tip, 10, (0, 255, 255), cv2.FILLED)
        cv2.circle(frame, middle_tip, 10, (255, 0, 255), cv2.FILLED)

        dist = np.linalg.norm(np.array(index_tip) - np.array(middle_tip))

        for btn in buttons:
            x, y = btn["pos"]
            if x < index_tip[0] < x + 80 and y < index_tip[1] < y + 60:
                cv2.rectangle(frame, (x-2, y-2), (x + 82, y + 62), glow, -1, lineType=cv2.LINE_AA)
                cv2.putText(frame, btn["label"], (x + 15, y + 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

                if dist < 40 and last_selected != btn["label"]:
                    last_selected = btn["label"]
                    label = btn["label"]
                    if label == "C":
                        expression = ""
                    elif label == "DEL":
                        if expression == "Error":
                            expression = ""
                        else:
                            expression = expression[:-1]
                    elif label == "^":
                        if history_scroll > 0:
                            history_scroll -= 1
                    elif label == "v":
                        if history_scroll < max(0, len(history) - 3):
                            history_scroll += 1
                    elif label == "=":
                        try:
                            safe_expr = re.sub(r'\b0+(\d+)', r'\1', expression)
                            result = str(eval(safe_expr))
                            history.append(f"{expression} = {result}")
                            expression = result
                            history_scroll = max(0, len(history) - 3)
                        except:
                            expression = "Error"
                    else:
                        expression += label

        if dist > 60:
            last_selected = ""

    if len(history) > 10:
        history = history[-10:]

    label_expr.config(text=expression)
    listbox_history.delete(0, tk.END)
    for item in history[history_scroll:history_scroll + 3]:
        listbox_history.insert(tk.END, item)

    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(image=img)
    frame_video.imgtk = imgtk
    frame_video.configure(image=imgtk)
    root.after(10, update_frame)

# Start loop
update_frame()
root.mainloop()
cap.release()
cv2.destroyAllWindows()
