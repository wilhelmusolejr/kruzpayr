from dotenv import load_dotenv
import requests
import os

load_dotenv()

RUNNER_ID = os.getenv("RUNNER_ID", "UNKNOWN")
SERVER_IP = os.getenv("SERVER_IP")

UPLOAD_IMAGE_URL = f"http://{SERVER_IP}:3001/upload-screenshot"
UPLOAD_TEXT_URL = f"http://{SERVER_IP}:3001/upload-textlog"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp"}
TEXT_EXTS = {".txt", ".log"}

def upload_and_delete(filepath):
    if not os.path.exists(filepath):
        return False
    
    ext = os.path.splitext(filepath)[1].lower()
    fileName = os.path.splitext(os.path.basename(filepath))[0]

    if ext in IMAGE_EXTS:
        upload_url = UPLOAD_IMAGE_URL
        file_key = "file"

    elif ext in TEXT_EXTS:
        upload_url = UPLOAD_TEXT_URL
        file_key = "file"

    else:
        print(f"❌ Unsupported file type: {ext}")
        return False

    try:
        with open(filepath, "rb") as f:
            res = requests.post(
                upload_url,
                files={file_key: f},
                data={
                    "runner": RUNNER_ID,
                    "fileName": fileName
                },
                timeout=10
            )

        if res.ok:
            os.remove(filepath)   # ✅ free VM disk
            return True
        else:
            print(f"❌ Upload failed ({res.status_code}): {res.text}")

    except Exception as e:
        print("❌ Upload exception:", e)

    return False
