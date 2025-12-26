from pathlib import Path

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

# --------------------------------------------------
# UI STATES
# --------------------------------------------------

UI_STATES = {
    "LOGIN": IMAGES_DIR / "login.png",
    "HOME": IMAGES_DIR / "home.png",
    "HOME_ADS": IMAGES_DIR / "home_ads.png",
    "LUCKY_DRAW": IMAGES_DIR / "lucky_draw.png",
}

# --------------------------------------------------
# THRESHOLDS & TIMING
# --------------------------------------------------

CHECK_INTERVAL = 5

LOGIN_FORM_THRESHOLD = 0.95
RANKMATCH_THRESHOLD = 0.65

# --------------------------------------------------
# API
# --------------------------------------------------

API_BASE = "http://192.168.131.250:3000/lucky-spin"
waitingTime = 30
