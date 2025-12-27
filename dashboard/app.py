from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from datetime import datetime
from werkzeug.utils import secure_filename
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DATA_SCREENSHOT_DIR = os.path.join(BASE_DIR, "log_data", "screenshots")
LOG_DATA_TEXTLOG_DIR = os.path.join(BASE_DIR, "log_data", "textlog")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/log", methods=["POST"])
def receive_log():
    data = request.get_json(silent=True) or {}

    log_entry = {
        "timestamp": datetime.utcnow().isoformat()
    }

    log_entry = {
        "level": data.get("level", "INFO"),
        "runner": data.get("runner", "unknown"),
        "message": data.get("message", ""),
        "time": data.get("time", datetime.now().strftime("%H:%M:%S")),
        "status": data.get("status", "UNKNOWN"),
        "username": data.get("username", "unknown"),
        "password": data.get("password", "UNKNOWN"),
        "ign": data.get("ign", "UNKNOWN"),
        
    }

    socketio.emit("log", log_entry)
    return jsonify({"ok": True})

@app.route("/upload-screenshot", methods=["POST"])
def upload_screenshot():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files["file"]
    runner = request.form.get("runner", "unknownRunner")
    fileName = request.form.get("fileName", "unknownFileName")

    runner_dir = os.path.join(LOG_DATA_SCREENSHOT_DIR, runner)
    os.makedirs(runner_dir, exist_ok=True)

    filename = secure_filename(f"{fileName}.png")

    save_path = os.path.join(runner_dir, filename)
    file.save(save_path)

    return jsonify({
        "ok": True,
        "path": save_path,
        "filename": filename
    })

@app.route("/upload-textlog", methods=["POST"])
def upload_textlog():
    """
    Accepts a text log file and saves it to log_data/text_logs
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    runner = request.form.get("runner", "unknownRunner")
    fileName = request.form.get("fileName", "unknownFileName")

    os.makedirs(LOG_DATA_TEXTLOG_DIR, exist_ok=True)

    filename = f"{fileName}_{runner}.txt"

    save_path = os.path.join(LOG_DATA_TEXTLOG_DIR, filename)
    file.save(save_path)

    return jsonify({
        "ok": True,
        "saved_as": filename
    })

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=3001, debug=True)
