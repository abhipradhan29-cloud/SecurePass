import os
import json
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import mysql.connector

# Initialize Flask
app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')
CORS(app)

# -----------------------------
# MySQL Connection
# -----------------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Abhiraaj@24",
        database="securepass"
    )

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
    return render_template('index.html')


@app.route('/api/report', methods=['POST'])
def api_report():
    data = request.get_json(silent=True)

    # ✅ Validate JSON
    if not isinstance(data, dict):
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    email = (data.get('email') or '').strip()
    message = (data.get('message') or '').strip()

    # ✅ Validation
    if not message:
        return jsonify({'success': False, 'error': 'Message required'}), 400

    if len(message) > 1000:
        return jsonify({'success': False, 'error': 'Message too long'}), 400

    if email and "@" not in email:
        return jsonify({'success': False, 'error': 'Invalid email'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # ✅ MySQL uses %s (NOT ?)
        cursor.execute(
            "INSERT INTO feedback (email, message) VALUES (%s, %s)",
            (email if email else None, message),
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        print("DB Error:", e)

        # Fallback to file
        try:
            append_feedback_fallback(email, message)
            return jsonify({'success': True, 'warning': 'Saved in fallback file'})
        except Exception:
            return jsonify({'success': False, 'error': 'Failed to save'}), 500


@app.route('/api/feedback', methods=['GET'])
def api_feedback():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, email, message, submitted_at FROM feedback ORDER BY submitted_at DESC"
        )

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'feedback': rows})

    except Exception as e:
        print("Fetch Error:", e)

        fallback = read_feedback_fallback()
        return jsonify({'success': True, 'feedback': fallback})


# -----------------------------
# Run App
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)