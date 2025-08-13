from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import hashlib
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'

NOTES_FILE = "my_notes.txt"
PASSWORD_FILE = "password.txt"

# --- Password Hash ---
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def load_notes():
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE, "r") as f:
        return [line.strip() for line in f.readlines()]

def save_note(note):
    with open(NOTES_FILE, "a") as f:
        f.write(note + "\n")

def overwrite_notes(notes):
    with open(NOTES_FILE, "w") as f:
        f.write("\n".join(notes) + "\n")

# --- Reminder Checker Thread ---
def check_reminders():
    while True:
        now = datetime.now()
        notes = load_notes()
        updated = False
        for i, line in enumerate(notes):
            if "[Reminder:" in line:
                try:
                    start = line.index("[Reminder: ") + len("[Reminder: ")
                    end = line.index("]", start)
                    rem_str = line[start:end]
                    rem_time = datetime.strptime(rem_str, "%Y-%m-%d %H:%M")
                    if rem_time <= now:
                        print(f"⏰ Reminder Alert Triggered: {line.strip()}")
                        notes[i] = line.replace(f" [Reminder: {rem_str}]", "")
                        updated = True
                except:
                    pass
        if updated:
            overwrite_notes(notes)
        time.sleep(60)

threading.Thread(target=check_reminders, daemon=True).start()

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if not os.path.exists(PASSWORD_FILE):
            return "No password set. Please create a password.txt file."
        with open(PASSWORD_FILE, "r") as f:
            saved_hash = f.read().strip()
        if hash_password(password) == saved_hash:
            session['logged_in'] = True
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="❌ Incorrect password")
    return render_template("login.html")

@app.route("/home")
def home():
    if not session.get("logged_in"):
        return redirect("/")
    return render_template("index.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/notes", methods=["GET"])
def get_notes():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(load_notes())

@app.route("/notes", methods=["POST"])
def add_note():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    text = data.get("text", "").strip()
    tags = data.get("tags", [])
    reminder = data.get("reminder", "")

    if not text:
        return jsonify({"error": "Note text is required"}), 400

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {text}"
    if tags:
        line += f" [Tags: {', '.join(tags)}]"
    if reminder:
        line += f" [Reminder: {reminder}]"
    save_note(line)
    return jsonify({"status": "saved"})

@app.route("/notes/<int:index>", methods=["DELETE"])
def delete_note(index):
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    notes = load_notes()
    if 0 <= index < len(notes):
        notes.pop(index)
        overwrite_notes(notes)
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Invalid index"}), 400

if __name__ == "__main__":
    app.run(debug=True)
