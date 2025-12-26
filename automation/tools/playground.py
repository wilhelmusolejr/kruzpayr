import pyautogui
import pydirectinput
import time 
import json
import sys

time.sleep(2)

print("Screen size at click time:", pyautogui.size())

def takeScreenshot(fileName):
    current_roi = pyautogui.screenshot()
    path = "logs/images/"
    current_roi.save(path + fileName + ".png")


takeScreenshot("test")


# --------------------
sys.exit()
# --------------------

