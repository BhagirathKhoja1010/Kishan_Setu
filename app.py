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
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_FILE = os.path.join(DATA_DIR, "db.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR, exist_ok=True)

app = Flask(
    __name__,
    static_folder=PUBLIC_DIR,
    static_url_path=""
)

CORS(app)


# =========================================================
# DEFAULT DATABASE
# =========================================================

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


# =========================================================
# DATABASE FUNCTIONS
# =========================================================

def save_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as file:
            json.dump(
                db,
                file,
                indent=2,
                ensure_ascii=False
            )
        return True

    except Exception as error:
        print("Database save error:", error)
        return False


def load_db():
    if not os.path.exists(DB_FILE):
        db = json.loads(json.dumps(DEFAULT_DB))
        save_db(db)
        return db

    try:
        with open(DB_FILE, "r", encoding="utf-8") as file:
            db = json.load(file)

        # Make sure required keys exist
        if "mandis" not in db:
            db["mandis"] = json.loads(
                json.dumps(DEFAULT_DB["mandis"])
            )

        if "crops" not in db:
            db["crops"] = json.loads(
                json.dumps(DEFAULT_DB["crops"])
            )

        if "slots" not in db:
            db["slots"] = json.loads(
                json.dumps(DEFAULT_DB["slots"])
            )

        if "bookings" not in db:
            db["bookings"] = []

        return db

    except Exception as error:
        print("Database load error:", error)

        db = json.loads(json.dumps(DEFAULT_DB))
        save_db(db)

        return db


# =========================================================
# HOME / FRONTEND
# =========================================================

@app.route("/")
def home():
    index_file = os.path.join(PUBLIC_DIR, "index.html")

    if os.path.exists(index_file):
        return send_from_directory(
            PUBLIC_DIR,
            "index.html"
        )

    return jsonify({
        "success": True,
        "message": "KisanSetu API is running",
        "frontend": "index.html not found in public folder"
    })


# =========================================================
# FRONTEND STATIC FILES
# =========================================================

@app.route("/<path:path>")
def static_files(path):

    # Don't interfere with API routes
    if path.startswith("api/"):
        return jsonify({
            "success": False,
            "message": "API endpoint not found"
        }), 404

    file_path = os.path.join(PUBLIC_DIR, path)

    if os.path.isfile(file_path):
        return send_from_directory(
            PUBLIC_DIR,
            path
        )

    # For frontend routes, return index.html
    index_file = os.path.join(PUBLIC_DIR, "index.html")

    if os.path.exists(index_file):
        return send_from_directory(
            PUBLIC_DIR,
            "index.html"
        )

    return jsonify({
        "success": False,
        "message": "Page not found"
    }), 404


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "status": "online",
        "service": "KisanSetu API",
        "time": datetime.now().isoformat()
    })


# =========================================================
# MANDIS
# =========================================================

@app.route("/api/mandis", methods=["GET"])
def get_mandis():

    db = load_db()

    return jsonify({
        "success": True,
        "mandis": db["mandis"]
    })


# =========================================================
# CROPS
# =========================================================

@app.route("/api/crops", methods=["GET"])
def get_crops():

    db = load_db()

    return jsonify({
        "success": True,
        "crops": db["crops"]
    })


# =========================================================
# SLOTS
# =========================================================

@app.route("/api/slots", methods=["GET"])
def get_slots():

    db = load_db()

    selected_date = request.args.get("date")
    mandi_id = request.args.get("mandi")

    result = []

    for slot in db["slots"]:

        booked_count = 0

        for booking in db["bookings"]:

            if (
                selected_date
                and mandi_id
                and booking.get("date") == selected_date
                and booking.get("mandi_id") == mandi_id
                and booking.get("slot") == slot
                and booking.get("status") != "Cancelled"
            ):
                booked_count += 1

        available = max(0, 10 - booked_count)

        result.append({
            "slot": slot,
            "booked": booked_count,
            "available": available,
            "capacity": 10,
            "is_available": available > 0
        })

    return jsonify({
        "success": True,
        "slots": result
    })


# =========================================================
# CREATE BOOKING
# =========================================================

@app.route("/api/bookings", methods=["POST"])
def create_booking():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid JSON data"
        }), 400

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

    # -----------------------------------------------------
    # REQUIRED FIELDS
    # -----------------------------------------------------

    for field in required_fields:

        value = data.get(field)

        if value is None or str(value).strip() == "":
            return jsonify({
                "success": False,
                "message": f"{field} is required"
            }), 400

    # -----------------------------------------------------
    # LOAD DATABASE
    # -----------------------------------------------------

    db = load_db()

    # -----------------------------------------------------
    # FIND MANDI
    # -----------------------------------------------------

    mandi = next(
        (
            item
            for item in db["mandis"]
            if item.get("id") == str(data["mandi_id"])
        ),
        None
    )

    if mandi is None:
        return jsonify({
            "success": False,
            "message": "Invalid mandi selected"
        }), 400

    # -----------------------------------------------------
    # FIND CROP
    # -----------------------------------------------------

    crop = next(
        (
            item
            for item in db["crops"]
            if item.get("id") == str(data["crop_id"])
        ),
        None
    )

    if crop is None:
        return jsonify({
            "success": False,
            "message": "Invalid crop selected"
        }), 400

    # -----------------------------------------------------
    # QUANTITY
    # -----------------------------------------------------

    try:
        quantity = float(data["quantity"])

    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Quantity must be a number"
        }), 400

    if quantity <= 0:
        return jsonify({
            "success": False,
            "message": "Quantity must be greater than zero"
        }), 400

    if quantity > 500:
        return jsonify({
            "success": False,
            "message": "Maximum quantity is 500 quintals"
        }), 400

    # -----------------------------------------------------
    # SLOT VALIDATION
    # -----------------------------------------------------

    if data["slot"] not in db["slots"]:
        return jsonify({
            "success": False,
            "message": "Invalid slot selected"
        }), 400

    # -----------------------------------------------------
    # DATE VALIDATION
    # -----------------------------------------------------

    booking_date = str(data["date"]).strip()

    try:
        datetime.strptime(
            booking_date,
            "%Y-%m-%d"
        )

    except ValueError:
        return jsonify({
            "success": False,
            "message": "Date must be in YYYY-MM-DD format"
        }), 400

    # -----------------------------------------------------
    # MOBILE
    # -----------------------------------------------------

    mobile = str(data["mobile"]).strip()

    if not mobile.isdigit() or len(mobile) != 10:
        return jsonify({
            "success": False,
            "message": "Mobile number must contain 10 digits"
        }), 400

    # -----------------------------------------------------
    # DUPLICATE BOOKING
    # -----------------------------------------------------

    for booking in db["bookings"]:

        if (
            booking.get("mobile") == mobile
            and booking.get("date") == booking_date
            and booking.get("status") != "Cancelled"
        ):

            return jsonify({
                "success": False,
                "message": (
                    "A booking already exists for "
                    "this mobile number on this date."
                )
            }), 409

    # -----------------------------------------------------
    # SLOT CAPACITY
    # -----------------------------------------------------

    same_slot_count = 0

    for booking in db["bookings"]:

        if (
            booking.get("date") == booking_date
            and booking.get("mandi_id") == mandi["id"]
            and booking.get("slot") == data["slot"]
            and booking.get("status") != "Cancelled"
        ):
            same_slot_count += 1

    if same_slot_count >= 10:

        return jsonify({
            "success": False,
            "message": (
                "This slot is full. "
                "Please select another slot."
            )
        }), 409

    # -----------------------------------------------------
    # ESTIMATED AMOUNT
    # -----------------------------------------------------

    msp = float(crop["msp"])

    estimated_amount = round(
        quantity * msp,
        2
    )

    # -----------------------------------------------------
    # BOOKING IDs
    # -----------------------------------------------------

    booking_id = str(uuid.uuid4()).replace(
        "-",
        ""
    )[:8].upper()

    token_number = (
        "KS-"
        + datetime.now().strftime("%y%m%d")
        + "-"
        + str(len(db["bookings"]) + 1).zfill(3)
    )

    # -----------------------------------------------------
    # BOOKING OBJECT
    # -----------------------------------------------------

    booking = {

        "booking_id": booking_id,

        "token": token_number,

        "farmer_name": str(
            data["farmer_name"]
        ).strip(),

        "mobile": mobile,

        "kisan_id": str(
            data.get("kisan_id", "")
        ).strip(),

        "mandi_id": mandi["id"],

        "mandi_name": mandi["name"],

        "district": mandi["district"],

        "state": mandi["state"],

        "crop_id": crop["id"],

        "crop_name": crop["name"],

        "crop_name_hi": crop["name_hi"],

        "quantity": quantity,

        "msp": msp,

        "estimated_amount": estimated_amount,

        "vehicle_type": str(
            data["vehicle_type"]
        ).strip(),

        "vehicle_number": str(
            data["vehicle_number"]
        ).upper().strip(),

        "date": booking_date,

        "slot": str(
            data["slot"]
        ).strip(),

        "village": str(
            data["village"]
        ).strip(),

        "bank_last4": str(
            data.get("bank_last4", "")
        ).strip(),

        "status": "Booked",

        "quality": {
            "status": "Pending",
            "moisture": None,
            "grade": None
        },

        "weighment": {
            "status": "Pending",
            "gross_weight": None,
            "tare_weight": None,
            "net_weight": None
        },

        "jform": {
            "status": "Pending",
            "generated_at": None
        },

        "dbt": {
            "status": "Pending",
            "amount": estimated_amount
        },

        "created_at": datetime.now().isoformat()
    }

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    db["bookings"].append(booking)

    if not save_db(db):

        return jsonify({
            "success": False,
            "message": "Could not save booking"
        }), 500

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return jsonify({
        "success": True,
        "message": "Slot booked successfully",
        "booking": booking
    }), 201


# =========================================================
# GET ALL BOOKINGS
# =========================================================

@app.route("/api/bookings", methods=["GET"])
def get_bookings():

    db = load_db()

    mobile = request.args.get("mobile")
    token = request.args.get("token")
    booking_id = request.args.get("booking_id")

    bookings = db["bookings"]

    # Search by mobile
    if mobile:
        bookings = [
            booking
            for booking in bookings
            if booking.get("mobile") == mobile
        ]

    # Search by token
    if token:
        bookings = [
            booking
            for booking in bookings
            if booking.get("token") == token
        ]

    # Search by booking ID
    if booking_id:
        bookings = [
            booking
            for booking in bookings
            if booking.get("booking_id") == booking_id
        ]

    return jsonify({
        "success": True,
        "count": len(bookings),
        "bookings": bookings
    })


# =========================================================
# GET SINGLE TOKEN
# =========================================================

@app.route("/api/token/<token>", methods=["GET"])
def get_token(token):

    db = load_db()

    booking = next(
        (
            item
            for item in db["bookings"]
            if item.get("token") == token
        ),
        None
    )

    if booking is None:

        return jsonify({
            "success": False,
            "message": "Token not found"
        }), 404

    return jsonify({
        "success": True,
        "booking": booking
    })


# =========================================================
# UPDATE BOOKING STATUS
# =========================================================

@app.route(
    "/api/bookings/<booking_id>/status",
    methods=["PUT"]
)
def update_status(booking_id):

    data = request.get_json(silent=True) or {}

    new_status = data.get("status")

    allowed_statuses = [
        "Booked",
        "Gate Entry",
        "Quality Check",
        "Weighment",
        "J-Form Generated",
        "DBT Paid",
        "Cancelled"
    ]

    if new_status not in allowed_statuses:

        return jsonify({
            "success": False,
            "message": "Invalid status"
        }), 400

    db = load_db()

    booking = next(
        (
            item
            for item in db["bookings"]
            if item.get("booking_id") == booking_id
        ),
        None
    )

    if booking is None:

        return jsonify({
            "success": False,
            "message": "Booking not found"
        }), 404

    booking["status"] = new_status

    if new_status == "DBT Paid":

        booking["dbt"]["status"] = "Paid"

    if not save_db(db):

        return jsonify({
            "success": False,
            "message": "Could not save status"
        }), 500

    return jsonify({
        "success": True,
        "message": "Status updated successfully",
        "booking": booking
    })


# =========================================================
# QUALITY CHECK
# =========================================================

@app.route(
    "/api/bookings/<booking_id>/quality",
    methods=["PUT"]
)
def update_quality(booking_id):

    data = request.get_json(silent=True) or {}

    db = load_db()

    booking = next(
        (
            item
            for item in db["bookings"]
            if item.get("booking_id") == booking_id
        ),
        None
    )

    if booking is None:

        return jsonify({
            "success": False,
            "message": "Booking not found"
        }), 404

    moisture = data.get("moisture")
    grade = data.get("grade")

    if moisture is not None:

        try:
            moisture = float(moisture)

        except (TypeError, ValueError):

            return jsonify({
                "success": False,
                "message": "Moisture must be a number"
            }), 400

    booking["quality"] = {

        "status": "Passed",

        "moisture": moisture,

        "grade": grade
    }

    booking["status"] = "Quality Check"

    if not save_db(db):

        return jsonify({
            "success": False,
            "message": "Could not save quality data"
        }), 500

    return j
