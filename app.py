from dotenv import load_dotenv
import os
import json
from datetime import datetime, timezone
import re

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import mysql.connector

load_dotenv()

#This line grabs the URL you just pasted to Render
db_url = os.getenv("DATABASE_URL")

print("RUNNING...")
print("🚀 STARTING APP...")

app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')
CORS(app)

# -----------------------------
# MySQL Connection (Railway FIXED)
# -----------------------------
def get_db_connection():
    try:
        print("🔌 Connecting to Railway MySQL...")

        conn = mysql.connector.connect(
            host=os.getenv("MYSQLHOST"),
            user=os.getenv("MYSQLUSER"),
            password=os.getenv("MYSQLPASSWORD"),
            database=os.getenv("MYSQLDATABASE"),
            port=int(os.getenv("MYSQLPORT", 3306)),
            connection_timeout=5
        )

        print("✅ MySQL Connected (Railway)!")
        return conn

    except Exception as e:
        print("❌ MySQL Connection Failed:", e)
        return None

# -----------------------------
# Fallback (if DB fails)
# -----------------------------
def get_feedback_fallback_path():
    return os.path.join(os.path.dirname(__file__), 'feedback_fallback.json')


def read_feedback_fallback():
    path = get_feedback_fallback_path()
    if not os.path.exists(path):
        return []

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def append_feedback_fallback(email, message):
    path = get_feedback_fallback_path()
    data = read_feedback_fallback()

    data.append({
        'email': email,
        'message': message,
        'submitted_at': datetime.now(timezone.utc).isoformat(),
        'fallback': True
    })

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

# -----------------------------
# Routes
# -----------------------------

@app.route('/')
def home():
    print("🏠 Home route accessed")
    return render_template('index.html')


@app.route('/api/report', methods=['POST'])
def api_report():
    print("📩 API /api/report called")

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    email = (data.get('email') or '').strip()
    message = (data.get('message') or '').strip()

    if not message:
        return jsonify({'success': False, 'error': 'Message required'}), 400

    if len(message) > 1000:
        return jsonify({'success': False, 'error': 'Message too long'}), 400

    if email and "@" not in email:
        return jsonify({'success': False, 'error': 'Invalid email'}), 400

    conn = get_db_connection()

    if not conn:
        print("⚠️ Using fallback file")
        append_feedback_fallback(email, message)
        return jsonify({'success': True, 'warning': 'Saved in fallback file'})

    try:
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO feedback (email, message) VALUES (%s, %s)",
            (email if email else None, message),
        )

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Data inserted into MySQL")

        return jsonify({'success': True})

    except Exception as e:
        print("❌ DB Insert Error:", e)
        append_feedback_fallback(email, message)
        return jsonify({'success': True, 'warning': 'Saved in fallback'})


@app.route('/api/feedback', methods=['GET'])
def api_feedback():
    print("📥 Fetching feedback")

    conn = get_db_connection()

    if not conn:
        print("⚠️ Using fallback for fetch")
        fallback = read_feedback_fallback()
        return jsonify({'success': True, 'feedback': fallback})

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, email, message, submitted_at FROM feedback ORDER BY submitted_at DESC"
        )

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'feedback': rows})

    except Exception as e:
        print("❌ Fetch Error:", e)
        fallback = read_feedback_fallback()
        return jsonify({'success': True, 'feedback': fallback})


# -----------------------------
# Run App
# -----------------------------
if __name__ == '__main__':
    print("🔥 RUNNING FLASK SERVER...")
    app.run(debug=True)