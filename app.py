from flask import Flask, request, jsonify, render_template
from database import init_db, get_db_connection
from datetime import datetime,timedelta,timezone
IST=timezone(timedelta(hours=5,minutes=30))

app = Flask(__name__)

# Initialize database
init_db()


# ==============================
# HOME PAGE
# ==============================

@app.route("/")
def home():
    return render_template("index.html")


# ==============================
# START CODING SESSION
# ==============================

@app.route("/start", methods=["POST"])
def start_session():

    data = request.get_json() or {}

    platform = data.get("platform")

    if not platform or not isinstance(platform, str):
        return jsonify({
            "error": "Platform is required."
        }), 400

    start_time = datetime.now(IST).isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO coding_sessions
        (platform, start_time)
        VALUES (?, ?)
        """,
        (platform, start_time)
    )

    session_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "session_id": session_id,
        "start_time": start_time
    }), 201


# ==============================
# STOP CODING SESSION
# ==============================

@app.route("/api/stop/<int:session_id>", methods=["POST"])
def stop_session(session_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, platform, start_time, end_time, duration
        FROM coding_sessions
        WHERE id = ?
        """,
        (session_id,)
    )

    row = cursor.fetchone()

    if row is None:

        conn.close()

        return jsonify({
            "error": "Session not found."
        }), 404

    if row["end_time"] is not None:

        conn.close()

        return jsonify({
            "error": "Session already stopped."
        }), 400

    start_time = datetime.fromisoformat(
        row["start_time"]
    )

    end_time = datetime.now(IST).isoformat()

    duration = int(
        (
            datetime.fromisoformat(end_time)
            - start_time
        ).total_seconds()
    )

    cursor.execute(
        """
        UPDATE coding_sessions
        SET end_time = ?, duration = ?
        WHERE id = ?
        """,
        (
            end_time,
            duration,
            session_id
        )
    )

    conn.commit()

    cursor.execute(
        """
        SELECT id, platform, start_time, end_time, duration
        FROM coding_sessions
        WHERE id = ?
        """,
        (session_id,)
    )

    updated_row = cursor.fetchone()

    conn.close()

    return jsonify({
        "id": updated_row["id"],
        "platform": updated_row["platform"],
        "start_time": updated_row["start_time"],
        "end_time": updated_row["end_time"],
        "duration": updated_row["duration"]
    })


# ==============================
# GET ALL SESSIONS
# ==============================

@app.route("/api/sessions", methods=["GET"])
def get_sessions():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, platform, start_time, end_time, duration
        FROM coding_sessions
        ORDER BY id
        """
    )

    sessions = [
        dict(row)
        for row in cursor.fetchall()
    ]

    conn.close()

    return jsonify(sessions)


# ==============================
# GET SESSIONS BY PLATFORM
# ==============================

@app.route("/api/sessions/<platform>", methods=["GET"])
def get_sessions_by_platform(platform):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, platform, start_time, end_time, duration
        FROM coding_sessions
        WHERE platform = ?
        ORDER BY id
        """,
        (platform,)
    )

    sessions = [
        dict(row)
        for row in cursor.fetchall()
    ]

    conn.close()

    return jsonify(sessions)


# ==============================
# DASHBOARD STATISTICS
# ==============================

@app.route("/api/stats", methods=["GET"])
def get_stats():

    conn = get_db_connection()
    cursor = conn.cursor()

    # Total sessions
    cursor.execute(
        """
        SELECT COUNT(*) AS total_sessions
        FROM coding_sessions
        """
    )

    total_sessions = cursor.fetchone()[
        "total_sessions"
    ]

    # Total coding duration
    cursor.execute(
        """
        SELECT COALESCE(SUM(duration), 0)
        AS total_duration
        FROM coding_sessions
        WHERE duration IS NOT NULL
        """
    )

    total_duration = cursor.fetchone()[
        "total_duration"
    ]

    # Most used platform by coding time
    cursor.execute(
        """
        SELECT platform,
               COALESCE(SUM(duration), 0)
               AS total_time
        FROM coding_sessions
        WHERE duration IS NOT NULL
        GROUP BY platform
        ORDER BY total_time DESC
        LIMIT 1
        """
    )

    top_platform = cursor.fetchone()

    conn.close()

    return jsonify({
        "total_sessions": total_sessions,

        "total_duration": total_duration,

        "top_platform": (
            top_platform["platform"]
            if top_platform
            else None
        ),

        "top_platform_time": (
            top_platform["total_time"]
            if top_platform
            else 0
        )
    })


# ==============================
# RUN FLASK APPLICATION
# ==============================
@app.route("/api/platform-stats", methods=["GET"])
def get_platform_stats():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT platform,
               COALESCE(SUM(duration), 0) AS total_time
        FROM coding_sessions
        WHERE duration IS NOT NULL
        GROUP BY platform
        ORDER BY total_time DESC
        """
    )

    platform_stats = [
        dict(row)
        for row in cursor.fetchall()
    ]

    conn.close()

    return jsonify(platform_stats)
@app.route("/api/daily-stats", methods=["GET"])
def get_daily_stats():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            DATE(start_time) AS date,
            COALESCE(SUM(duration), 0) AS total_time,
            COUNT(*) AS sessions
        FROM coding_sessions
        WHERE duration IS NOT NULL
        GROUP BY DATE(start_time)
        ORDER BY date DESC
    """)

    daily_stats = [
        dict(row)
        for row in cursor.fetchall()
    ]

    conn.close()

    return jsonify(daily_stats)
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)