import pyautogui
import pydirectinput
import time 
import json
import sys

with open("keyboard.json", "r") as f:
    coords = json.load(f)

data = {
    "username": "carmen683",
    "password": "boktitelo1",
    "ign": "666.3570.627"
}

time.sleep(2)

print("Screen size at click time:", pyautogui.size())


# --------------------
sys.exit()
# --------------------

