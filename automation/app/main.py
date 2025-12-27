from dotenv import load_dotenv
from app.log import upload_and_delete
from datetime import datetime
from PIL import ImageGrab, Image
from skimage.metrics import structural_similarity as ssim
from config.config import (
    DATABASE_PATH,
    EXE_PATH,
    GAME_PROCESS_NAME,
    LOGIN_FORM_REF,
    LOGIN_FORM_THRESHOLD,
    MODAL_REF,
    LUCKY_NOT_CLICKABLE_REF,
    CHECK_INTERVAL,
    API_BASE,
    errorLeft,
    UI_LAYOUT_PATH,
    STATUS_THRESHOLD,
    IP_WAIT_SECONDS,
    DASHBOARD_API,
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
import os

load_dotenv()

resolution = "800x600"
RUNNER_ID = os.getenv("RUNNER_ID", "UNKNOWN")

# Log
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"{timestamp}_{RUNNER_ID}_log.txt"

LOG_DIR = "logs"
log_path = os.path.join(LOG_DIR, log_filename)
os.makedirs(LOG_DIR, exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------

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
modal_home_ads =  (215, 193, 586, 355)
modal_home = (250, 202, 546, 391)

GLOBAL_STATUS = "init"

# ----------------------------------------------------
# FUNCTIONS
# ----------------------------------------------------

def send_log(level, message):
    current_time = datetime.now().strftime("%H:%M:%S")
    username = data["username"] if "data" in globals() else "unknown"
    password = data["password"] if "data" in globals() else "unknown"
    ign = data["ign"] if "data" in globals() else "unknown"

    try:
        requests.post(
            f"{DASHBOARD_API}/log",
            json={
                "level": level,
                "runner": RUNNER_ID,
                "message": message,
                "time": current_time,
                "status": GLOBAL_STATUS,
                "username": username,
                "password": password,
                "ign": ign
            },
            timeout=3
        )
    except Exception:
        pass  # never crash bot because of dashboard

def abort(reason):
    global GLOBAL_STATUS
    GLOBAL_STATUS = "ABORT"

    logging.error(f"ABORT: {reason}")
    send_log("ERROR", f"ABORT: {reason}")
    try:
        name = data.get("username", "unknown")
        takeScreenshot(f"{name}_{reason}")
    except Exception:
        pass
    close_crossfire_window()
    return False

def start_launcher():
    if not os.path.exists(EXE_PATH):

        # log 
        sms = "EXE not found"
        logging.error(sms)
        send_log("ERROR", sms)
        
        return False

    # Kill patcher if already running
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == "patcher_cf2.exe":
                
                # Log
                sms = "Existing patcher found, terminating..."
                logging.info(sms)
                send_log("INFO", sms)
                
                proc.kill()
                proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    time.sleep(1)  # give Windows time to release handles

    sms = "Starting launcher..."
    logging.info(sms)
    send_log("INFO", sms)

    os.startfile(EXE_PATH)
    return True

def is_process_running(process_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
            return True
    return False

def wait_for_game_process():
    # log
    sms = "Waiting for game process..."
    logging.info(sms)
    send_log("INFO", sms)

    counterLeft = 5
    while counterLeft > 0:
        if is_process_running(GAME_PROCESS_NAME):
            sms = "Game process detected"
            logging.info(sms)
            send_log("INFO", sms)
            return True
        
        time.sleep(5)
        counterLeft -= 1

    sms = "Game process not detected"
    logging.error(sms)
    send_log("ERROR", sms)

    return False

def login_form_visible():
    try:
        x1, y1, x2, y2 = login_form_roi

        # Safety check
        if x2 <= x1 or y2 <= y1:
            logging.error(f"Invalid ROI: {login_form_roi}")
            send_log("ERROR", f"Invalid ROI: {login_form_roi}")
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
            send_log("WARNING", f"ROI size mismatch: {current_gray.shape} vs {reference_gray.shape}")
            return False

        score, _ = ssim(current_gray, reference_gray, full=True)
        logging.debug(f"Login form similarity: {score:.2f}")
        send_log("INFO", f"Login form similarity: {score:.2f}")

        return score >= LOGIN_FORM_THRESHOLD

    except Exception as e:
        logging.error(f"Login form check error: {e}")
        send_log("ERROR", f"Login form check error: {e}")
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
        send_log("WARNING", f"ROI size mismatch: {current_gray.shape} vs {reference_gray.shape}")
        return False

    score, _ = ssim(current_gray, reference_gray, full=True)
    logging.info(f"LUCKY SPIN BUTTON similarity: {score:.2f}")
    send_log("INFO", f"LUCKY SPIN BUTTON similarity: {score:.2f}")

    return score >= LOGIN_FORM_THRESHOLD

def focus_window_by_title(keyword, timeout=10):
    logging.info(f"Attempting to focus window with title containing '{keyword}' (timeout: {timeout}s)")
    send_log("INFO", f"Attempting to focus window with title containing '{keyword}' (timeout: {timeout}s)")
    end_time = time.time() + timeout

    while time.time() < end_time:
        windows = gw.getWindowsWithTitle(keyword)
        if windows:
            win = windows[0]
            logging.info(f"Found window: '{win.title}'")
            send_log("INFO", f"Found window: '{win.title}'")

            if win.isMinimized:
                logging.info("Window is minimized, restoring")
                send_log("INFO", "Window is minimized, restoring")
                win.restore()

            send_log("INFO", "Activating window")
            win.activate()
            time.sleep(0.5)
            logging.info("Window focused successfully")
            return True

        time.sleep(0.5)

    logging.warning(f"Could not find window with title containing '{keyword}' within {timeout} seconds")
    return False

def close_all_crossfire_windows():
    sms = "Searching for all CrossFire windows to close"
    logging.info(sms)
    send_log("INFO", sms)
    
    windows = gw.getWindowsWithTitle("CrossFire")
    if not windows:
        sms = "No CrossFire windows found"
        logging.warning(sms)
        send_log("WARNING", sms)

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
        send_log("INFO", f"CrossFire cleanup complete (killed {killed} processes)")
        return True

    sms = "No CrossFire windows or processes found"
    logging.info(sms)
    send_log("INFO", sms)
    return False

def isModalExist():
    x1, y1, x2, y2 = modal_home
    width = x2 - x1
    height = y2 - y1   

    current_roi = pyautogui.screenshot(region=(x1, y1, width, height))
    reference = Image.open(MODAL_REF)

    current_gray = np.array(current_roi.convert("L"))
    reference_gray = np.array(reference.convert("L"))

    if current_gray.shape != reference_gray.shape:
        logging.warning(f"ROI size mismatch: {current_gray.shape} vs {reference_gray.shape}")
        send_log("WARNING", f"ROI size mismatch: {current_gray.shape} vs {reference_gray.shape}")
        return False

    score, _ = ssim(current_gray, reference_gray, full=True)
    logging.info(f"MODAL BUTTON similarity: {score:.2f}")
    send_log("INFO", f"MODAL BUTTON similarity: {score:.2f}")

    return score >= LOGIN_FORM_THRESHOLD 

def isModalExistHomeAds():
    x1, y1, x2, y2 = modal_home
    width = x2 - x1
    height = y2 - y1   

    current_roi = pyautogui.screenshot(region=(x1, y1, width, height))
    reference = Image.open(MODAL_REF)

    current_gray = np.array(current_roi.convert("L"))
    reference_gray = np.array(reference.convert("L"))

    if current_gray.shape != reference_gray.shape:
        logging.warning(f"ROI size mismatch: {current_gray.shape} vs {reference_gray.shape}")
        send_log("WARNING", f"ROI size mismatch: {current_gray.shape} vs {reference_gray.shape}")
        return False

    score, _ = ssim(current_gray, reference_gray, full=True)
    logging.info(f"Home ads modal similarity: {score:.2f}")
    send_log("INFO", f"Home ads modal similarity: {score:.2f}")

    return score >= LOGIN_FORM_THRESHOLD  

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
        logging.info(f"{status} similarity: {score:.2f}")

        if score > best_score:
            best_score = score
            best_status = status

    if best_score < STATUS_THRESHOLD:
        return "UNKNOWN", best_score

    return best_status, best_score

def takeScreenshot(fileName=None):
    # Ensure folders exist
    path = "logs/images"
    os.makedirs(path, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Build filename
    if fileName:
        final_name = f"{fileName}_{timestamp}.png"
    else:
        final_name = f"{timestamp}.png"

    file_path = os.path.join(path, final_name)

    # Take screenshot
    screenshot = pyautogui.screenshot()
    screenshot.save(file_path)

    # Upload & delete
    upload_and_delete(
        filepath=file_path
    )

    msg = f"Screenshot captured: {final_name}"
    logging.info(msg)
    send_log("INFO", msg)

def get_current_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=30).text.strip()
    except Exception:
        return None

def wait_for_ip_change(user_info):
    sms = "IP marked as bad. Need to change IP."
    logging.warning(sms)
    send_log("WARNING", sms)

    old_ip = user_info["ip"]

    while True:
        sms = "Waiting 10 minutes before checking IP again..."
        logging.info(sms)
        send_log("INFO", sms)
        time.sleep(IP_WAIT_SECONDS)

        new_ip = get_current_ip()
        logging.info(f"Current IP after wait: {new_ip}")
        send_log("INFO", f"Current IP after wait: {new_ip}")

        if not new_ip:
            sms = "Failed to fetch IP, retrying..."
            logging.warning(sms)
            send_log("WARNING", sms)
            continue

        if new_ip == old_ip:
            sms = "IP has not changed. Need to change IP."
            logging.warning(sms)
            send_log('WARNING', sms)
            continue

        # IP changed ✅
        logging.info(f"IP changed from {old_ip} → {new_ip}")
        send_log("INFO", f"IP changed from {old_ip} → {new_ip}")
        user_info["ip"] = new_ip
        user_info["status"] = "initial"
        return True

def main():
    global GLOBAL_STATUS

    logging.info(f"Screen size at click time: {pyautogui.size()}")
    time.sleep(2)
    sms = "Starting main automation sequence"
    send_log("INFO", "--------------")
    send_log("INFO", sms)
    logging.info(sms)

    start_launcher()

    if not wait_for_game_process():
        abort("game did not start")
        return False

    sms = "Waiting for login form to appear..."
    logging.info(sms)
    send_log("INFO", sms)
    
    # initial to look for login
    clickLeft = 15
    while clickLeft > 0:
        if not login_form_visible():
            logging.info(f"Login form not found, retrying... ({clickLeft-1} attempts left)")
            send_log("INFO", f"Login form not found ... {clickLeft-1}/15")
            clickLeft -= 1
            time.sleep(CHECK_INTERVAL)

            if clickLeft == 0:
                abort("Login form not found")
                return False
            
            continue
        
        sms = "Login form detected successfully"
        logging.info(sms)
        send_log("INFO", sms)
        break

    good = True
    last_status = None
    same_status_count = 0
    MAX_SAME_STATUS = 5

    while good:
        status, confidence = getCurrentStatus()

        GLOBAL_STATUS = status

        logging.info(f"Current status: {status} with confidence {confidence:.2f}")
        send_log("INFO", f"Current status: {status} with confidence {confidence:.2f}")

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
                    logging.info(f"Login form not found, retrying... ({clickLeft-1} attempts left)")
                    send_log("INFO", f"Login form not found ... {clickLeft-1}/15")
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
            send_log("INFO", f"Typing username: {data['username']}")
            pyautogui.write(data['username'], interval=0.05)

            time.sleep(2)

            # PASSWORD
            x, y = coords['passwordInput']
            logging.info(f"Moving to password input field at ({x}, {y})")
            pydirectinput.moveTo( x, y)
            time.sleep(0.1)
            logging.info("Clicking password input field")
            pydirectinput.click()
            logging.info("Typing password")
            send_log("INFO", f"Typing password: **********")
            pyautogui.write(data['password'], interval=0.05)

            time.sleep(1)

            # LOGIN
            x, y = coords['loginButton']
            logging.info(f"Moving to login button at ({x}, {y})")
            pydirectinput.moveTo( x, y)
            time.sleep(0.1)
            sms = "Clicking login button"
            logging.info(sms)
            send_log("INFO", sms)
            pydirectinput.click()

            logging.info("Waiting 5 seconds after login attempt")
            time.sleep(5)
        
        elif status == "IGN":
            sms = "Entering IGN input state"
            logging.info(sms)
            send_log("INFO", sms)

            # input ign
            x, y = coords['ignInput']
            logging.info(f"Moving to IGN input field at ({x}, {y})")
            pydirectinput.moveTo(x, y)
            time.sleep(0.1)
            logging.info("Clicking IGN input field")
            pydirectinput.click()
            logging.info(f"Typing IGN: {data['ign']}")
            send_log("INFO", f"Typing IGN: {data['ign']}")
            pyautogui.write(data['ign'], interval=0.05)
            time.sleep(1)

            # confirm
            x, y = coords['ignButtonConfirm']
            logging.info(f"Moving to IGN confirm button at ({x}, {y})")
            pydirectinput.moveTo(x, y)
            time.sleep(0.1)
            sms = "Clicking IGN confirm button"
            logging.info(sms)
            send_log("INFO", sms)
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
            sms = "Clicking IGN okay button"
            logging.info(sms)
            send_log("INFO", sms)
            pydirectinput.click()

        elif status == "BUY_CHAR":
            sms = "Entering BUY_CHAR state"
            logging.info(sms)
            send_log("INFO", sms)

             # BUY CHAR
            x, y = coords['buyCharacterButton']
            logging.info(f"Moving to buy character button at ({x}, {y})")
            pydirectinput.moveTo(x, y)
            time.sleep(0.1)
            sms = "Clicking buy character button"
            logging.info(sms)
            send_log("INFO", sms)

            pydirectinput.click()

            time.sleep(1)
            
            sms = "Pressing ENTER key (1/2)"
            logging.info(sms)
            send_log("INFO", sms)
            pyautogui.press("enter")
            time.sleep(1)

            sms = "Pressing ENTER key (2/2)"
            logging.info(sms)
            send_log("INFO", sms)
            pyautogui.press("enter")

        elif status == "HOME_ADS":

            sms = "Entering HOME_ADS state"
            logging.info(sms)
            send_log("INFO", sms)

            time.sleep(5)

            if isModalExistHomeAds():
                sms = "Found modal in home ads"
                logging.info(sms)
                send_log("INFO", sms)
                pydirectinput.moveTo( x, y)
                
                time.sleep(1)

                x, y = coords['modalHomeAds']
                pydirectinput.moveTo( x, y)
                time.sleep(0.1)

            time.sleep(1)
            sms = "Pressing ESC to close ads"
            logging.info(sms)
            send_log("INFO", sms)
            pyautogui.press("esc")
            time.sleep(1)
        
        elif status == "HOME":
            sms = "Entering HOME state"
            logging.info(sms)
            send_log("INFO", sms)

            time.sleep(5)

            if isModalExist():
                x, y = coords['confirmPurchaseCompleteButton']

                logging.info("Found modal in home")
                send_log("INFO", "Found modal in home")
                pydirectinput.moveTo( x, y)
                
                time.sleep(1)

            pyautogui.press("enter")
            time.sleep(1)

            pyautogui.press("enter")
            time.sleep(1)

            # PRESS LUCKY LOGO
            x, y = coords['luckSpinLogoButton']
            logging.info(f"Moving to lucky spin logo button at ({x}, {y})")
            pydirectinput.moveTo( x, y)
            time.sleep(0.1)

            sms = "Clicking lucky spin logo button"
            logging.info(sms)
            send_log("INFO", sms)
            pydirectinput.click()

            # PRESS FREE SPIN
            x, y = coords['useFreeSpinButton']
            logging.info(f"Moving to use free spin button at ({x}, {y})")
            pydirectinput.moveTo( x, y)
            time.sleep(0.1)
            sms = "Clicking use free spin button"
            logging.info(sms)
            send_log("INFO", sms)
            pydirectinput.click()

            clickLeft = 10
            logging.info(f"Starting free spin attempts (max {clickLeft})")
            while clickLeft > 0:
                if isNotClickable():
                    sms = "Lucky spin button is not clickable, stopping attempts"
                    logging.info(sms)
                    send_log("INFO", sms)
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
                send_log("INFO", "Waiting 10 seconds before next attempt.")
                time.sleep(10)

            sms = "Free spin process completed"
            logging.info(sms)
            send_log("INFO", sms)

            good = False

        else:
            sms = "Unknown UI state, waiting..."
            logging.warning(sms)
            send_log("INFO", sms)

        time.sleep(10)

    # ----------------------------------------------------
    # EXIT
    logging.info("Starting exit sequence")
    time.sleep(10)

    sms = "Closing CrossFire window"
    logging.info(sms)
    send_log("INFO", sms)
    close_crossfire_window()

    time.sleep(10)

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
counter = 1
toUpload = 10
while errorLeft > 0:
    logging.info(f"Loading backend jobs. Errors left: {errorLeft}")

    if toUpload == 0:
        upload_and_delete(log_path)
        toUpload = 10

    try:
        res = requests.get(f"{API_BASE}/next", timeout=waitingTime)

        if res.status_code == 404:
            sms = "No Lucky Spin jobs available. Sleeping..."
            logging.info(sms)
            send_log("INFO", sms)
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

    success = main()
    GLOBAL_STATUS = "initial"

    try:
        if success:

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
            sms = "Success detected, resetting error counter to 3"
            logging.info(sms)
            send_log("INFO", sms)

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
            send_log('WARNING', f"Failure detected. errorLeft={errorLeft}")

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
    counter += 1
    toUpload -= 1




