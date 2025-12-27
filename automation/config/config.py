from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

SERVER_IP = os.getenv("SERVER_IP")

# --------------------------------------------------
# PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = PROJECT_ROOT / "database" / "database.csv"
IMAGES_DIR = PROJECT_ROOT / "images"

UI_LAYOUT_PATH = PROJECT_ROOT / "config" / "ui_layout.json"
UI_STATES_PATH = PROJECT_ROOT / "config" / "ui_states.json"
# --------------------------------------------------
# GAME
# --------------------------------------------------

EXE_PATH = r"C:\Program Files (x86)\Crossfire PH\patcher_cf2.exe"
GAME_PROCESS_NAME = "crossfire.exe"

# --------------------------------------------------
# IMAGE REFERENCES
# --------------------------------------------------

INPUT_IGN_REF = IMAGES_DIR / "input_ign.png"
LUCKY_NOT_CLICKABLE_REF = IMAGES_DIR / "not_clickable.png"
RANK_MATCH_REF = IMAGES_DIR / "rankMatchUi.png"
LOGIN_FORM_REF = IMAGES_DIR / "roi_test.png"
MODAL_REF = IMAGES_DIR / "modal_ref.png"

# --------------------------------------------------
# UI STATES
# --------------------------------------------------


# --------------------------------------------------
# THRESHOLDS & TIMING
# --------------------------------------------------


LOGIN_FORM_THRESHOLD = 0.95
RANKMATCH_THRESHOLD = 0.65

# --------------------------------------------------
# API
# --------------------------------------------------

API_BASE = f"http://{SERVER_IP}:3000/lucky-spin"
DASHBOARD_API = f"http://{SERVER_IP}:3001"

# -------------------------
waitingTime = 30
STATUS_THRESHOLD = 0.80
IP_WAIT_SECONDS = 10 * 60 
errorLeft = 3
CHECK_INTERVAL = 5
