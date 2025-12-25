import pyautogui
import time
import keyboard
import psutil
import os
import json
import cv2
import numpy as np
import sys
import pydirectinput
import pygetwindow as gw
import pandas as pd

from PIL import ImageGrab, Image
from skimage.metrics import structural_similarity as ssim

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------

EXE_PATH = r"C:\Program Files (x86)\Crossfire PH\patcher_cf2.exe"
GAME_PROCESS_NAME = "crossfire.exe"
INPUT_IGN_REF = "input_ign.png"
LUCKY_NOT_CLICKABLE_REF = "not_clickable.png"
RANK_MATCH_REF = "rankMatchUi.png"
CHECK_INTERVAL = 5               

LOGIN_FORM_ROI = (460, 330, 860, 730)
LOGIN_FORM_REF = "roi_test.png"
LOGIN_FORM_THRESHOLD = 0.95
RANKMATCH_THRESHOLD = 0.65

UI_STATES = {
    "LOGIN": "images/login.png",
    "HOME": "images/home.png",
    "HOME_ADS": "images/home_ads.png",
    "LUCKY_DRAW": "images/lucky_draw.png"
}

with open("keyboard.json", "r") as f:
    coords = json.load(f)
		
# ----------------------------------------------------
# FUNCTIONS
# ----------------------------------------------------

def abort(reason):
    print(f"🛑 ABORT: {reason}")
    return False

def start_launcher():
    if not os.path.exists(EXE_PATH):
        print("❌ EXE not found")
        return False

    # Kill patcher if already running
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == "patcher_cf2.exe":
                print("🛑 Existing patcher found, terminating...")
                proc.kill()
                proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    time.sleep(1)  # give Windows time to release handles

    print("🚀 Starting launcher...")
    os.startfile(EXE_PATH)

    return True

def is_process_running(process_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
            return True
    return False

def wait_for_game_process():
    print("⏳ Waiting for game process...")

    counterLeft = 5
    while counterLeft > 0:
        if is_process_running(GAME_PROCESS_NAME):
            print("✅ Game process detected")
            return True
        
        time.sleep(5)
        counterLeft -= 1

    print("❌ Game process not detected")
    return False

def login_form_visible():
    try:
        x1, y1, x2, y2 = LOGIN_FORM_ROI

        # Safety check
        if x2 <= x1 or y2 <= y1:
            print("❌ Invalid ROI:", LOGIN_FORM_ROI)
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
            print("⚠ ROI size mismatch",
                  current_gray.shape, reference_gray.shape)
            return False

        score, _ = ssim(current_gray, reference_gray, full=True)
        print(f"🔍 Login form similarity: {score:.3f}")

        return score >= LOGIN_FORM_THRESHOLD

    except Exception as e:
        print("❌ Login form check error:", e)
        return False

def pointerGetter():
    print("Move mouse to target.")
    print("Press F8 to print X,Y")
    print("Press ESC to quit")

    while True:
        if keyboard.is_pressed("f8"):
            x, y = pyautogui.position()
            print(f"X: {x}, Y: {y}")
            time.sleep(0.3)  # debounce

        if keyboard.is_pressed("esc"):
            print("Exiting...")
            break

def isAccountNew():
    current_roi = pyautogui.screenshot()
    reference = Image.open(INPUT_IGN_REF)

    current_gray = np.array(current_roi.convert("L"))
    reference_gray = np.array(reference.convert("L"))

    if current_gray.shape != reference_gray.shape:
        print("⚠ ROI size mismatch", current_gray.shape, reference_gray.shape)
        return False

    score, _ = ssim(current_gray, reference_gray, full=True)
    print(f"🔍 IS ACCOUNT NEW: {score:.3f}")

    return score >= LOGIN_FORM_THRESHOLD

def isNotClickable():
    x1, y1, x2, y2 = (401, 545, 704, 654)
    width = x2 - x1
    height = y2 - y1

    current_roi = pyautogui.screenshot(region=(x1, y1, width, height))
    reference = Image.open(LUCKY_NOT_CLICKABLE_REF)

    current_gray = np.array(current_roi.convert("L"))
    reference_gray = np.array(reference.convert("L"))

    if current_gray.shape != reference_gray.shape:
        print("⚠ ROI size mismatch", current_gray.shape, reference_gray.shape)
        return False

    score, _ = ssim(current_gray, reference_gray, full=True)
    print(f"🔍 LUCKY SPIN BUTTON: {score:.3f}")

    return score >= LOGIN_FORM_THRESHOLD

def focus_window_by_title(keyword, timeout=10):
    """
    Brings the first window containing `keyword` in its title to the front.
    """
    end_time = time.time() + timeout

    while time.time() < end_time:
        windows = gw.getWindowsWithTitle(keyword)
        if windows:
            win = windows[0]

            if win.isMinimized:
                win.restore()

            win.activate()
            time.sleep(0.5)
            return True

        time.sleep(0.5)

    return False

def isThereRankMatcUi():
    current_roi = pyautogui.screenshot()
    reference = Image.open(RANK_MATCH_REF)

    current_gray = np.array(current_roi.convert("L"))
    reference_gray = np.array(reference.convert("L"))

    if current_gray.shape != reference_gray.shape:
        print("⚠ ROI size mismatch", current_gray.shape, reference_gray.shape)
        return False

    score, _ = ssim(current_gray, reference_gray, full=True)
    print(f"🔍 isThereRank: {score:.3f}")

    return score >= RANKMATCH_THRESHOLD

def close_crossfire_window():
    windows = gw.getWindowsWithTitle("CrossFire")
    if not windows:
        print("❌ CrossFire window not found")
        return False

    win = windows[0]
    win.close()   # graceful close
    time.sleep(2)
    return True

def image_similarity(img1, img2):
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    img1_gray = cv2.resize(img1_gray, (img2_gray.shape[1], img2_gray.shape[0]))

    diff = cv2.absdiff(img1_gray, img2_gray)
    score = 1 - (np.mean(diff) / 255)

    return score

STATUS_THRESHOLD = 0.80
def getCurrentStatus():
    screenshot = pyautogui.screenshot()
    current = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    best_status = "UNKNOWN"
    best_score = 0.0

    for status, img_path in UI_STATES.items():
        ref = cv2.imread(img_path)
        if ref is None:
            continue

        score = image_similarity(current, ref)
        print(f"🔍 {status}: {score:.3f}")

        if score > best_score:
            best_score = score
            best_status = status

    if best_score < STATUS_THRESHOLD:
        return "UNKNOWN", best_score

    return best_status, best_score

def main(): 
    print("Screen size at click time:", pyautogui.size())
    time.sleep(2)
    print("START")

    start_launcher()

    if not wait_for_game_process():
        abort("game did not start")
        return False

    print("🔍 Waiting for login form...")

    status, confidence = getCurrentStatus()
    print("📍 Current status:", status, confidence)

    if status == "LOGIN":
        clickLeft = 15
        while clickLeft > 0:
            if not login_form_visible():
                print("⌛ Login form not found, retrying...")
                clickLeft -= 1
                time.sleep(CHECK_INTERVAL)

                if clickLeft == 0:
                    abort("Login form not found")
                    return False

                continue

            print("✅ Login form shown")

            # allow UI to settle
            time.sleep(2)

            print("🎯 Bringing CrossFire to front...")
            focused = focus_window_by_title("crossfire")

            if not focused:
                print("⚠ Could not focus CrossFire window")

            # ---- WAIT FOR RESOLUTION TO STABILIZE ----
            prev_size = pyautogui.size()
            while True:
                time.sleep(1)
                curr_size = pyautogui.size()
                if curr_size == prev_size:
                    break
                prev_size = curr_size

            print("🖥 Stable screen size:", curr_size)

            # ---- FORCE INPUT ACCEPTANCE (DYNAMIC CENTER) ----
            screen_w, screen_h = curr_size
            center_x = screen_w // 2
            center_y = screen_h // 2

            pydirectinput.moveTo(center_x, center_y)
            time.sleep(0.2)
            pydirectinput.click()
            time.sleep(0.5)

            print("🎯 Input focus confirmed")
            break

        # USERNAME
        x, y = coords['usernameInput']
        pydirectinput.moveTo( x, y)
        time.sleep(0.1)
        pydirectinput.click()
        pyautogui.write(data['username'], interval=0.05)

        time.sleep(1)

        # PASSWORD
        x, y = coords['passwordInput']
        pydirectinput.moveTo( x, y)
        time.sleep(0.1)
        pydirectinput.click()
        pyautogui.write(data['password'], interval=0.05)

        time.sleep(1)

        # LOGIN
        x, y = coords['loginButton']
        pydirectinput.moveTo( x, y)
        time.sleep(0.1)
        pydirectinput.click()

        time.sleep(10)
        
    elif status == "IGN":
        # input ign
        x, y = coords['ignInput']
        pydirectinput.moveTo(x, y)
        time.sleep(0.1)
        pydirectinput.click()
        pyautogui.write(data['ign'], interval=0.05)

        time.sleep(1)

        # confirm
        x, y = coords['ignButtonConfirm']
        pydirectinput.moveTo(x, y)
        time.sleep(0.1)
        pydirectinput.click()
        time.sleep(1)
        pydirectinput.click()

        time.sleep(1)

        # Okay ign
        x, y = coords['ignOkayButton']
        pydirectinput.moveTo(x, y)
        time.sleep(0.1)
        pydirectinput.click()

        time.sleep(5)

        # BUY CHAR
        x, y = coords['buyCharacterButton']
        pydirectinput.moveTo(x, y)
        time.sleep(0.1)
        pydirectinput.click()

        time.sleep(1)

        # 3 esc. 
        pyautogui.press("esc")
        time.sleep(1)
        pyautogui.press("esc")
        time.sleep(1)
        pyautogui.press("enter")
        time.sleep(1)
        pyautogui.press("enter")
    elif status == "BUY_CHAR":
        handle_buy_char()
    elif status == "HOME_ADS":
        close_ads()
    else:
        print("⚠ Unknown UI state, waiting...")


        


    if isAccountNew():
        

    else:
        print("not new account")

    time.sleep(5)

    if isThereRankMatcUi():
        time.sleep(1)
        pyautogui.press("esc")
        time.sleep(1)

    else:
        print("no ui")


    # PRESS LUCKY LOGO
    x, y = coords['luckSpinLogoButton']
    pydirectinput.moveTo( x, y)
    time.sleep(0.1)
    pydirectinput.click()

    # PRESS FREE SPIN
    x, y = coords['useFreeSpinButton']
    pydirectinput.moveTo( x, y)
    time.sleep(0.1)
    pydirectinput.click()

    clickLeft = 10
    while clickLeft > 0:
        if isNotClickable():
            break

        # PRESS FREE SPIN
        x, y = coords['useFreeSpinButton']
        pydirectinput.moveTo(x, y)
        time.sleep(0.1)
        pydirectinput.click()

        clickLeft -= 1
        time.sleep(10)

    # EXIT
    time.sleep(10)
    close_crossfire_window()
    time.sleep(10)

    return True

# ----------------------------------------------------
# MAIN
# ----------------------------------------------------

errorLeft = 3
while errorLeft > 0:
    df = pd.read_csv("database.csv")
    toProcessDf = df[(df["CLAIMED_LUCKY"] == False) & (df["STATUS"] == "undefined") & (df["ECOIN"] > 0)].sample(n=1)
    account = toProcessDf.iloc[0]
    index = account.name  
    
    data = {
        'username': account['USERNAME'],
        'password': account['PASSWORD'],
        'ign': account['IGN']
    }

    print("Username:", data['username'])
    print("Password:", data['password'])
    print("IGN     :", data['ign'])

    success = main()
    df.loc[index, 'CLAIMED_LUCKY'] = bool(success)
    df.loc[index, 'STATUS'] = "complete" if success else "error"
    df.to_csv("database.csv", index=False)

    if not success:
        errorLeft -= 1
    else: 
        errorLeft = 3