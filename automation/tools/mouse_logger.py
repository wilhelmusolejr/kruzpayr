import pyautogui
import keyboard
import time

print("🖱 Mouse position recorder")
print("Press F8 to log mouse (x, y)")
print("Press ESC to exit")

while True:
    if keyboard.is_pressed("f8"):
        x, y = pyautogui.position()
        print(f"X: {x}, Y: {y}")
        time.sleep(0.3)  # debounce so it doesn't spam

    if keyboard.is_pressed("esc"):
        print("Exiting...")
        break
