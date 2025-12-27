import pyautogui
import pydirectinput
import time 
import json
import sys
import requests
import logging

time.sleep(2)

x1, y1, x2, y2 = (215, 193, 586, 355)

# Safety check
if x2 <= x1 or y2 <= y1:
    logging.error(f"Invalid ROI: {login_form_roi}")
    send_log("ERROR", f"Invalid ROI: {login_form_roi}")

width = x2 - x1
height = y2 - y1

current_roi = pyautogui.screenshot(
    region=(x1, y1, width, height)
)

current_roi.save("test.png")  # debug



# --------------------
sys.exit()
# --------------------





