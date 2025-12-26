import requests
import os

UPLOAD_URL = "http://192.168.131.250:3001/upload-screenshot"

def upload_and_delete(filepath, username, runner):
    if not os.path.exists(filepath):
        return False

    try:
        with open(filepath, "rb") as f:
            res = requests.post(
                UPLOAD_URL,
                files={"file": f},
                data={
                    "username": username,
                    "runner": runner
                },
                timeout=10
            )

        if res.ok:
            os.remove(filepath)  # ✅ free VM disk
            return True

    except Exception as e:
        print("Upload failed:", e)

    return False


upload_and_delete("buy_char.png", "test", "VM1")