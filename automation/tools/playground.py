import pyautogui
import pydirectinput
import time 
import json
import sys
import requests
import logging

time.sleep(2)

RUNNER_ID = "VM1"
DASHBOARD_API = "http://localhost:3001"

print("Screen size at click time:", pyautogui.size())

def send_log(level, message):
    try:
        requests.post(
            f"{DASHBOARD_API}/log",
            json={
                "level": level,
                "message": message,
                "runner": RUNNER_ID
            },
            timeout=3
        )
    except Exception:
        pass  # never crash bot because of dashboard

send_log("INFO", "Login started")
send_log("ERROR", "Login failed")

# --------------------
sys.exit()
# --------------------





