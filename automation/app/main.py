from config.config import (
    DATABASE_PATH,
    EXE_PATH,
    GAME_PROCESS_NAME,
    UI_STATES,
    LOGIN_FORM_REF,
    LOGIN_FORM_THRESHOLD,
    LUCKY_NOT_CLICKABLE_REF,
    CHECK_INTERVAL,
    API_BASE,
    UI_LAYOUT_PATH,
    UI_STATES_PATH,
    waitingTime
)

import pygetwindow as gw
import pandas as pd
import numpy as np
import pyautogui
import time
import keyboard
import psutil
import os
import json
import cv2
import sys
import pydirectinput
import logging
import requests

from PIL import ImageGrab, Image
from skimage.metrics import structural_similarity as ssim

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs.txt'),
        logging.StreamHandler()
    ]
)

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------

resolution = "800x600"

with open(UI_STATES_PATH, "r") as f:
    UI_STATES = json.load(f)

with open(UI_LAYOUT_PATH, "r") as f:
    ui_layout = json.load(f)

coords = ui_layout["resolution"][resolution]["keyboard"]

UI_STATE_IMAGES = {
    state: cv2.imread(path)
    for state, path in UI_STATES.items()
}

login_form_roi = (282, 330, 521, 585)
lucky_button_roi = (264, 477, 440, 533)

STATUS_THRESHOLD = 0.80
errorLeft = 3
IP_WAIT_SECONDS = 10 * 60 

# ----------------------------------------------------
# FUNCTIONS
# ----------------------------------------------------

def abort(reason):
    logging.error(f"ABORT: {reason}")
    try:
        name = data.get("username", "unknown")
        takeScreenshot(f"{name}_{reason}")
    except Exception:
        pass
    close_crossfire_window()
    return False

def start_launcher():
    if not os.path.exists(EXE_PATH):
        logging.error("EXE not found")
        return False

    # Kill patcher if already running
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == "patcher_cf2.exe":
                logging.info("Existing patcher found, terminating...")
                proc.kill()
                proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    time.sleep(1)  # give Windows time to release handles

    logging.info("Starting launcher...")
    os.startfile(EXE_PATH)

    return True

def is_process_running(process_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
            return True
    return False

def wait_for_game_process():
    logging.info("Waiting for game process...")

    counterLeft = 5
    while counterLeft > 0:
        if is_process_running(GAME_PROCESS_NAME):
            logging.info("Game process detected")
            return True
        
        time.sleep(5)
        counterLeft -= 1

    logging.error("Game process not detected")
    return False

def login_form_visible():
    try:
        x1, y1, x2, y2 = login_form_roi

        # Safety check
        if x2 <= x1 or y2 <= y1:
            logging.error(f"Invalid ROI: {login_form_roi}")
            return False

        width = x2 - x1
        height = y2 - y1

        current_roi = pyautogui.screenshot(
            region=(x1, y1, width, height)
        )

        # current_roi.save("test.png")  # debug

        reference = Image.open(LOGIN_FORM_REF)

        current_gray = np.array(current_roi.convert("L"))
        reference_gray = np.array(reference.convert("L"))

        if current_gray.shape != reference_gray.shape:
            logging.warning(f"ROI size mismatch: {current_gray.shape} vs {reference_gray.shape}")
            return False

        score, _ = ssim(current_gray, reference_gray, full=True)
        logging.info(f"Login form similarity: {score:.3f}")

        return score >= LOGIN_FORM_THRESHOLD

    except Exception as e:
        logging.error(f"Login form check error: {e}")
        return False

def isNotClickable():
    x1, y1, x2, y2 = lucky_button_roi
    width = x2 - x1
    height = y2 - y1

    current_roi = pyautogui.screenshot(region=(x1, y1, width, height))
    reference = Image.open(LUCKY_NOT_CLICKABLE_REF)

    current_gray = np.array(current_roi.convert("L"))
    reference_gray = np.array(reference.convert("L"))

    if current_gray.shape != reference_gray.shape:
        logging.warning(f"ROI size mismatch: {current_gray.shape} vs {reference_gray.shape}")
        return False

    score, _ = ssim(current_gray, reference_gray, full=True)
    logging.info(f"LUCKY SPIN BUTTON similarity: {score:.3f}")

    return score >= LOGIN_FORM_THRESHOLD

def focus_window_by_title(keyword, timeout=10):
    """
    Brings the first window containing `keyword` in its title to the front.
    """
    logging.info(f"Attempting to focus window with title containing '{keyword}' (timeout: {timeout}s)")
    end_time = time.time() + timeout

    while time.time() < end_time:
        windows = gw.getWindowsWithTitle(keyword)
        if windows:
            win = windows[0]
            logging.info(f"Found window: '{win.title}'")

            if win.isMinimized:
                logging.info("Window is minimized, restoring")
                win.restore()

            logging.info("Activating window")
            win.activate()
            time.sleep(0.5)
            logging.info("Window focused successfully")
            return True

        time.sleep(0.5)

    logging.warning(f"Could not find window with title containing '{keyword}' within {timeout} seconds")
    return False

# def close_crossfire_window():
#     logging.info("Searching for CrossFire window to close")
#     windows = gw.getWindowsWithTitle("CrossFire")
#     if not windows:
#         logging.error("CrossFire window not found")
#         return False

#     win = windows[0]
#     logging.info(f"Found CrossFire window: '{win.title}', closing gracefully")
#     win.close()   # graceful close
#     logging.info("Waiting 2 seconds for window to close")
#     time.sleep(2)
#     logging.info("CrossFire window closed successfully")
#     return True


def close_all_crossfire_windows():
    logging.info("Searching for all CrossFire windows to close")
    
    windows = gw.getWindowsWithTitle("CrossFire")
    if not windows:
        logging.warning("No CrossFire windows found")
        return False

    closed_count = 0

    for win in windows:
        try:
            logging.info(f"Closing window: '{win.title}'")

            if win.isMinimized:
                win.restore()
                time.sleep(0.2)

            win.close()
            closed_count += 1

            time.sleep(0.5)  # small delay between closes

        except Exception as e:
            logging.error(f"Failed to close window '{win.title}': {e}")

    logging.info(f"Closed {closed_count}/{len(windows)} CrossFire windows")
    return closed_count > 0

def close_crossfire_window():
    closed_window = close_all_crossfire_windows()

    killed = 0
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info["name"] and "crossfire" in proc.info["name"].lower():
                logging.warning(f"Killing process {proc.info['name']} (PID {proc.pid})")
                proc.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if closed_window or killed > 0:
        logging.info(f"CrossFire cleanup complete (killed {killed} processes)")
        return True

    logging.error("No CrossFire windows or processes found")
    return False

def image_similarity(img1, img2):
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    img1_gray = cv2.resize(img1_gray, (img2_gray.shape[1], img2_gray.shape[0]))

    diff = cv2.absdiff(img1_gray, img2_gray)
    score = 1 - (np.mean(diff) / 255)

    return score

def getCurrentStatus():
    screenshot = pyautogui.screenshot()
    current = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    best_status = "UNKNOWN"
    best_score = 0.0

    for status, img_path in UI_STATES.items():
        ref = UI_STATE_IMAGES.get(status)
        if ref is None:
            continue

        score = image_similarity(current, ref)
        logging.info(f"{status} similarity: {score:.3f}")

        if score > best_score:
            best_score = score
            best_status = status

    if best_score < STATUS_THRESHOLD:
        return "UNKNOWN", best_score

    return best_status, best_score

def takeScreenshot(fileName):
    current_roi = pyautogui.screenshot()
    path = "logs/images/"
    current_roi.save(path + fileName + ".png")
    logging.info("Done screenshot")

def get_current_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=30).text.strip()
    except Exception:
        return None

def wait_for_ip_change(user_info):
    logging.warning("IP marked as bad. Need to change IP.")

    old_ip = user_info["ip"]

    while True:
        logging.info("Waiting 10 minutes before checking IP again...")
        time.sleep(IP_WAIT_SECONDS)

        new_ip = get_current_ip()
        logging.info(f"Current IP after wait: {new_ip}")

        if not new_ip:
            logging.warning("Failed to fetch IP, retrying...")
            continue

        if new_ip == old_ip:
            logging.warning("IP has not changed. Need to change IP.")
            continue

        # IP changed ✅
        logging.info(f"IP changed from {old_ip} → {new_ip}")
        user_info["ip"] = new_ip
        user_info["status"] = "initial"
        return True

def main(): 
    logging.info(f"Screen size at click time: {pyautogui.size()}")
    time.sleep(2)
    logging.info("Starting main automation sequence")

    start_launcher()

    if not wait_for_game_process():
        abort("game did not start")
        return False

    logging.info("Waiting for login form to appear...")
    
    # initial to look for login
    clickLeft = 15
    while clickLeft > 0:
        if not login_form_visible():
            logging.info(f"Login form not found, retrying... ({clickLeft-1} attempts left)")
            clickLeft -= 1
            time.sleep(CHECK_INTERVAL)

            if clickLeft == 0:
                abort("Login form not found")
                return False
            
            continue
        
        logging.info("Login form detected successfully")
        break

    good = True
    last_status = None
    same_status_count = 0
    MAX_SAME_STATUS = 5

    while good:
        status, confidence = getCurrentStatus()

        logging.info(f"Current status: {status} with confidence {confidence}")

        if status == last_status:
            same_status_count += 1
        else:
            if last_status is not None:
                logging.info(f"STATE CHANGE: {last_status} → {status}")
            same_status_count = 1
            last_status = status

        logging.info(f"{status} repeated {same_status_count} times")

        if same_status_count >= MAX_SAME_STATUS:
            abort(f"Stuck on state {status} for too long")
            return False

        # CONDITIONALS

        if status == "LOGIN":

            clickLeft = 15
            while clickLeft > 0:
                if not login_form_visible():
                    logging.info(f"Login form not visible in LOGIN state, retrying... ({clickLeft-1} attempts left)")
                    clickLeft -= 1
                    time.sleep(CHECK_INTERVAL)

                    if clickLeft == 0:
                        abort("Login form not found")
                        return False
                    
                    continue
                    
                break
                    
            logging.info("Login form confirmed visible in LOGIN state")

            # allow UI to settle
            logging.info("Waiting 2 seconds for UI to settle")
            time.sleep(2)

            logging.info("Bringing CrossFire to front...")
            focused = focus_window_by_title("crossfire")

            if not focused:
                logging.warning("Could not focus CrossFire window")

            # ---- WAIT FOR RESOLUTION TO STABILIZE ----
            prev_size = pyautogui.size()
            while True:
                time.sleep(1)
                curr_size = pyautogui.size()
                if curr_size == prev_size:
                    break
                prev_size = curr_size

            logging.info(f"Stable screen size: {curr_size}")

            # ---- FORCE INPUT ACCEPTANCE (DYNAMIC CENTER) ----
            screen_w, screen_h = curr_size
            center_x = screen_w // 2
            center_y = screen_h // 2

            pydirectinput.moveTo(center_x, center_y)
            time.sleep(0.2)
            pydirectinput.click()
            time.sleep(0.5)

            logging.info("Input focus confirmed")

            # USERNAME
            x, y = coords['usernameInput']
            logging.info(f"Moving to username input field at ({x}, {y})")
            pydirectinput.moveTo( x, y)
            time.sleep(0.1)
            logging.info("Clicking username input field")
            pydirectinput.click()
            logging.info(f"Typing username: {data['username']}")
            pyautogui.write(data['username'], interval=0.05)

            time.sleep(1)

            # PASSWORD
            x, y = coords['passwordInput']
            logging.info(f"Moving to password input field at ({x}, {y})")
            pydirectinput.moveTo( x, y)
            time.sleep(0.1)
            logging.info("Clicking password input field")
            pydirectinput.click()
            logging.info("Typing password")
            pyautogui.write(data['password'], interval=0.05)

            time.sleep(1)

            # LOGIN
            x, y = coords['loginButton']
            logging.info(f"Moving to login button at ({x}, {y})")
            pydirectinput.moveTo( x, y)
            time.sleep(0.1)
            logging.info("Clicking login button")
            pydirectinput.click()

            logging.info("Waiting 5 seconds after login attempt")
            time.sleep(5)
        
        elif status == "IGN":
            logging.info("Entering IGN input state")
            # input ign
            x, y = coords['ignInput']
            logging.info(f"Moving to IGN input field at ({x}, {y})")
            pydirectinput.moveTo(x, y)
            time.sleep(0.1)
            logging.info("Clicking IGN input field")
            pydirectinput.click()
            logging.info(f"Typing IGN: {data['ign']}")
            pyautogui.write(data['ign'], interval=0.05)

            time.sleep(1)

            # confirm
            x, y = coords['ignButtonConfirm']
            logging.info(f"Moving to IGN confirm button at ({x}, {y})")
            pydirectinput.moveTo(x, y)
            time.sleep(0.1)
            logging.info("Clicking IGN confirm button")
            pydirectinput.click()
            time.sleep(1)
            logging.info("Double-clicking IGN confirm button")
            pydirectinput.click()

            time.sleep(1)

            # Okay ign
            x, y = coords['ignOkayButton']
            logging.info(f"Moving to IGN okay button at ({x}, {y})")
            pydirectinput.moveTo(x, y)
            time.sleep(0.1)
            logging.info("Clicking IGN okay button")
            pydirectinput.click()

        elif status == "BUY_CHAR":
            logging.info("Entering BUY_CHAR state")
             # BUY CHAR
            x, y = coords['buyCharacterButton']
            logging.info(f"Moving to buy character button at ({x}, {y})")
            pydirectinput.moveTo(x, y)
            time.sleep(0.1)
            logging.info("Clicking buy character button")
            pydirectinput.click()

            time.sleep(1)

            # 3 esc. 
            logging.info("Pressing ESC key (1/3)")
            pyautogui.press("esc")
            time.sleep(1)
            logging.info("Pressing ESC key (2/3)")
            pyautogui.press("esc")
            time.sleep(1)
            logging.info("Pressing ENTER key (1/2)")
            pyautogui.press("enter")
            time.sleep(1)
            logging.info("Pressing ENTER key (2/2)")
            pyautogui.press("enter")

        elif status == "HOME_ADS":
            logging.info("Entering HOME_ADS state")
            time.sleep(1)
            logging.info("Pressing ESC to close ads")
            pyautogui.press("esc")
            time.sleep(1)
        
        elif status == "HOME":
            logging.info("Entering HOME state")
            # PRESS LUCKY LOGO
            x, y = coords['luckSpinLogoButton']
            logging.info(f"Moving to lucky spin logo button at ({x}, {y})")
            pydirectinput.moveTo( x, y)
            time.sleep(0.1)
            logging.info("Clicking lucky spin logo button")
            pydirectinput.click()

            # PRESS FREE SPIN
            x, y = coords['useFreeSpinButton']
            logging.info(f"Moving to use free spin button at ({x}, {y})")
            pydirectinput.moveTo( x, y)
            time.sleep(0.1)
            logging.info("Clicking use free spin button")
            pydirectinput.click()

            clickLeft = 10
            logging.info(f"Starting free spin attempts (max {clickLeft})")
            while clickLeft > 0:
                if isNotClickable():
                    logging.info("Lucky spin button is not clickable, stopping attempts")
                    takeScreenshot(data['username'] + data['ign'] + " login")
                    break

                # PRESS FREE SPIN
                x, y = coords['useFreeSpinButton']
                logging.info(f"Attempting free spin click {11-clickLeft}/10 at ({x}, {y})")
                pydirectinput.moveTo(x, y)
                time.sleep(0.1)
                logging.info("Clicking use free spin button")
                pydirectinput.click()

                clickLeft -= 1
                logging.info(f"Waiting 10 seconds before next attempt. Attempts left: {clickLeft}")
                time.sleep(10)

            logging.info("Free spin process completed")
            good = False

        else:
            logging.warning("Unknown UI state, waiting...")

        time.sleep(10)

    # ----------------------------------------------------
    # EXIT
    logging.info("Starting exit sequence")
    time.sleep(10)
    logging.info("Closing CrossFire window")
    close_crossfire_window()
    logging.info("Waiting 10 seconds after closing")
    time.sleep(10)
    logging.info("Automation completed successfully")

    return True

# ----------------------------------------------------
# MAIN
# ----------------------------------------------------

# get current IP address
user_info = {
    "ip": get_current_ip(),
    "status": "initial"  # initial | bad
}

logging.info("Starting main account processing loop")
while errorLeft > 0:
    logging.info(f"Loading backend jobs. Errors left: {errorLeft}")

    try:
        res = requests.get(f"{API_BASE}/next", timeout=waitingTime)

        if res.status_code == 404:
            logging.info("No Lucky Spin jobs available. Sleeping...")
            time.sleep(10)
            continue

        res.raise_for_status()
        job = res.json()

    except requests.exceptions.RequestException as e:
        logging.error(f"Backend request failed: {e}")
        errorLeft -= 1
        time.sleep(5)
        continue

    job_id = job["jobId"]
    account = job["account"]

    data = {
        "username": account["username"],
        "password": account["password"],
        "ign": account["ign"]
    }

    logging.info(f"Selected account for processing: {data['username']}")
    logging.info(f"Username: {data['username']}")
    logging.info(f"Password: {data['password']}")
    logging.info(f"IGN: {data['ign']}")

    logging.info("Starting main automation process")
    success = main()
    
    try:
        if success:
            logging.info("Automation completed successfully")

            requests.patch(
                f"{API_BASE}/{job_id}",
                json={
                    "status": "success",
                    "isClaimed": True,
                    "claimedAt": time.strftime("%Y-%m-%dT%H:%M:%S")
                },
                timeout=waitingTime
            )

            errorLeft = 3
            logging.info("Success detected, resetting error counter to 3")

        else:
            logging.error("Automation failed")

            requests.patch(
                f"{API_BASE}/{job_id}",
                json={
                    "status": "failed"
                },
                timeout=waitingTime
            )

            errorLeft -= 1
            logging.warning(f"Failure detected. errorLeft={errorLeft}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to update job status: {e}")
        errorLeft -= 1

    if errorLeft <= 0:
        user_info["status"] = "bad"

    # 🔴 IP is bad → do NOT run bot
    if user_info["status"] == "bad":
        recovered = wait_for_ip_change(user_info)

        if recovered:
            errorLeft = 1 
            user_info["status"] = "initial"
            logging.info("Retrying with new IP...")
        continue

    time.sleep(5)




