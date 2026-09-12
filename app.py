import os
import json
import uuid
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS


# =========================================================
# FLASK APP
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=BASE_DIR,
    static_url_path=""
)

CORS(app)


# =========================================================
# DATABASE
# =========================================================

DB_FILE = os.path.join(BASE_DIR, "db.json")


DEFAULT_DB = {
    "mandis": [
        {
            "id": "M001",
            "name": "Karnal Procurement Mandi",
            "district": "Karnal",
            "state": "Haryana"
        },
        {
            "id": "M002",
            "name": "Panipat Grain Market",
            "district": "Panipat",
            "state": "Haryana"
        },
        {
            "id": "M003",
            "name": "Kurukshetra Grain Market",
            "district": "Kurukshetra",
            "state": "Haryana"
        },
        {
            "id": "M004",
            "name": "Jaipur Agriculture Mandi",
            "district": "Jaipur",
            "state": "Rajasthan"
        },
        {
            "id": "M005",
            "name": "Kota Grain Market",
            "district": "Kota",
            "state": "Rajasthan"
        }
    ],

    "crops": [
        {
            "id": "C001",
            "name": "Wheat",
            "name_hi": "गेहूं",
            "msp": 2275
        },
        {
            "id": "C002",
            "name": "Paddy",
            "name_hi": "धान",
            "msp": 2369
        },
        {
            "id": "C003",
            "name": "Mustard",
            "name_hi": "सरसों",
            "msp": 5950
        },
        {
            "id": "C004",
            "name": "Gram",
            "name_hi": "चना",
            "msp": 5650
        },
        {
            "id": "C005",
            "name": "Maize",
            "name_hi": "मक्का",
            "msp": 2400
        },
        {
            "id": "C006",
            "name": "Soybean",
            "name_hi": "सोयाबीन",
            "msp": 5328
        },
        {
            "id": "C007",
            "name": "Cotton",
            "name_hi": "कपास",
            "msp": 7710
        }
    ],

    "slots": [
        "09:00 AM - 11:00 AM",
        "11:00 AM - 01:00 PM",
        "02:00 PM - 04:00 PM",
        "04:00 PM - 06:00 PM"
    ],

    "bookings": []
}


def load_db():
    """
    Load database from db.json.
    If file does not exist or is corrupted,
    create/use default database.
    """

    if not os.path.exists(DB_FILE):
        save_db(DEFAULT_DB)
        return DEFAULT_DB

    try:
        with open(DB_FILE, "r", encoding="utf-8") as file:
            db = json.load(file)

        # Make sure required keys exist
        db.setdefault("mandis", DEFAULT_DB["mandis"])
        db.setdefault("crops", DEFAULT_DB["crops"])
        db.setdefault("slots", DEFAULT_DB["slots"])
        db.setdefault("bookings", [])

        return db

    except Exception:
        save_db(DEFAULT_DB)
        return DEFAULT_DB


def save_db(db):
    """
    Save database to db.json.
    """

    with open(DB_FILE, "w", encoding="utf-8") as file:
        json.dump(
            db,
            file,
            indent=2,
            ensure_ascii=False
        )


# =========================================================
# HOME / FRONTEND
# =========================================================

@app.route("/")
def home():
    return send_from_directory(
        BASE_DIR,
        "index.html"
    )


# =========================================================
# FRONTEND STATIC FILES
# =========================================================

@app.route("/<path:filename>")
def static_files(filename):

    # Do not expose Python/database files
    blocked_files = [
        "app.py",
        "db.json",
        "requirements.txt",
        "render.yaml"
    ]

    if filename in blocked_files:
        return jsonify({
            "success": False,
            "message": "File not accessible"
        }), 404

    file_path = os.path.join(BASE_DIR, filename)

    if os.path.isfile(file_path):
        return send_from_directory(
            BASE_DIR,
            filename
        )

    return jsonify({
        "success": False,
        "message": "File not found"
    }), 404


# =========================================================
# MASTER DATA - MANDIS
# =========================================================

@app.route("/api/mandis", methods=["GET"])
def get_mandis():

    db = load_db()

    return jsonify(
        db["mandis"]
    )


# =========================================================
# MASTER DATA - CROPS
# =========================================================

@app.route("/api/crops", methods=["GET"])
def get_crops():

    db = load_db()

    return jsonify(
        db["crops"]
    )


# =========================================================
# MASTER DATA - SLOTS
# =========================================================

@app.route("/api/slots", methods=["GET"])
def get_slots():

    db = load_db()

    selected_date = request.args.get("date")
    mandi_id = request.args.get("mandi")

    booked = []

    if selected_date and mandi_id:

        for booking in db["bookings"]:

            if (
                booking.get("date") == selected_date
                and booking.get("mandi_id") == mandi_id
                and booking.get("status") != "Cancelled"
            ):
                booked.append(
                    booking.get("slot")
                )

    result = []

    for slot in db["slots"]:

        count = booked.count(slot)

        result.append({
            "slot": slot,
            "booked": count,
            "available": max(0, 10 - count),
            "is_available": count < 10
        })

    return jsonify(result)


# =========================================================
# CREATE BOOKING
# =========================================================

@app.route("/api/bookings", methods=["POST"])
def create_booking():

    data = request.get_json(silent=True) or {}

    required_fields = [
        "farmer_name",
        "mobile",
        "mandi_id",
        "crop_id",
        "quantity",
        "vehicle_type",
        "vehicle_number",
        "date",
        "slot",
        "village"
    ]

    # Check required fields
    for field in required_fields:

        if not data.get(field):

            return jsonify({
                "success": False,
                "message": f"{field} is required"
            }), 400

    db = load_db()

    # =====================================================
    # FIND MANDI
    # =====================================================

    mandi = next(
        (
            m for m in db["mandis"]
            if m["id"] == data["mandi_id"]
        ),
        None
    )

    if not mandi:

        return jsonify({
            "success": False,
            "message": "Invalid mandi selected"
        }), 400

    # =====================================================
    # FIND CROP
    # =====================================================

    crop = next(
        (
            c for c in db["crops"]
            if c["id"] == data["crop_id"]
        ),
        None
    )

    if not crop:

        return jsonify({
            "success": False,
            "message": "Invalid crop selected"
        }), 400

    # -----------------------------
# QUANTITY
# -----------------------------

try:
    quantity = float(data["quantity"])
except (ValueError, TypeError):
    return jsonify({
        "success": False,
        "message": "Quantity must be a number"
    }), 400

if quantity <= 0 or quantity > 500:
    return jsonify({
        "success": False,
        "message": "Quantity must be between 1 and 500 quintals"
    }), 400
