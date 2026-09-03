from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, text, inspect
from datetime import datetime
import hashlib
import secrets
import hmac
from backend.models import (
    Donor,
    Hospital,
    BloodRequest,
    Notification,
    PushSubscription
)
from backend.database import Base, engine, SessionLocal
from backend.location import calculate_distance
from backend.notification_service import send_push_notification


# =========================================================
# MATCHING RADIUS (km)
# Donors within this distance from the hospital get notified.
# =========================================================

MATCH_RADIUS_KM = 20

# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password: str) -> str:

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    )

    return (
        salt.hex()
        + ":"
        + password_hash.hex()
    )


def verify_password(password: str, stored_password: str) -> bool:

    try:

        salt_hex, hash_hex = stored_password.split(":")

        salt = bytes.fromhex(salt_hex)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100000
        )

        return hmac.compare_digest(
            password_hash.hex(),
            hash_hex
        )

    except Exception:

        return False


# =========================================================
# AI DONOR RANKING
# Combines 3 signals into one 0-100 "match score":
#   - Distance (50%)   : closer to the hospital = higher
#   - Reliability (30%): donor's past accept-rate on
#                        notifications = higher
#   - Age fit (20%)    : 18-45 is prime donor age, tapering
#                        off outside that range
# New donors with no history get a neutral reliability score
# so they aren't unfairly penalised on their first request.
# =========================================================

def get_donor_accept_reject_counts(db, donor_id):

    accepted = (
        db.query(Notification)
        .filter(
            Notification.donor_id == donor_id,
            Notification.status == "accepted"
        )
        .count()
    )

    rejected = (
        db.query(Notification)
        .filter(
            Notification.donor_id == donor_id,
            Notification.status == "rejected"
        )
        .count()
    )

    return accepted, rejected


def calculate_reliability_score(accepted, rejected):

    total = accepted + rejected

    if total == 0:
        return 70.0

    return round((accepted / total) * 100, 1)


def calculate_age_score(age):

    if age is None:
        return 60.0

    if 18 <= age <= 45:
        return 100.0

    if 46 <= age <= 60:
        return 75.0

    return 40.0


def calculate_distance_score(distance_km, radius_km):

    if distance_km is None:
        return 60.0

    ratio = max(0.0, 1 - (distance_km / radius_km))

    return round(ratio * 100, 1)


def calculate_match_score(distance_km, radius_km, age, accepted, rejected):

    distance_component = calculate_distance_score(distance_km, radius_km)

    reliability_component = calculate_reliability_score(accepted, rejected)

    age_component = calculate_age_score(age)

    score = (
        (distance_component * 0.5)
        + (reliability_component * 0.3)
        + (age_component * 0.2)
    )

    return round(score, 1)


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# DATABASE MIGRATION
# ADD REQUIRED COLUMNS IF THEY DO NOT EXIST
# =========================================================

try:
    inspector = inspect(engine)

    # -----------------------------------------------------
    # DONOR TABLE
    # -----------------------------------------------------

    if "donors" in inspector.get_table_names():

        donor_columns = [
            column["name"]
            for column in inspector.get_columns("donors")
        ]

        if "password" not in donor_columns:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        ALTER TABLE donors
                        ADD COLUMN password VARCHAR(255)
                        """
                    )
                )

            print("Donor password column added successfully.")

        else:
            print("Donor password column already exists.")

    # -----------------------------------------------------
    # HOSPITAL TABLE
    # -----------------------------------------------------

    if "hospitals" in inspector.get_table_names():

        hospital_columns = [
            column["name"]
            for column in inspector.get_columns("hospitals")
        ]

        # Add email column
        if "email" not in hospital_columns:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        ALTER TABLE hospitals
                        ADD COLUMN email VARCHAR(150)
                        """
                    )
                )

            print("Hospital email column added successfully.")

        else:
            print("Hospital email column already exists.")

        # Add password column
        if "password" not in hospital_columns:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        ALTER TABLE hospitals
                        ADD COLUMN password VARCHAR(255)
                        """
                    )
                )

            print("Hospital password column added successfully.")

        else:
            print("Hospital password column already exists.")

    # -----------------------------------------------------
    # NOTIFICATIONS TABLE
    # -----------------------------------------------------

    if "notifications" in inspector.get_table_names():

        notif_columns = [
            column["name"]
            for column in inspector.get_columns("notifications")
        ]

        if "match_score" not in notif_columns:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        ALTER TABLE notifications
                        ADD COLUMN match_score FLOAT
                        """
                    )
                )

            print("match_score column added successfully.")

        if "match_rank" not in notif_columns:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        ALTER TABLE notifications
                        ADD COLUMN match_rank INTEGER
                        """
                    )
                )

            print("match_rank column added successfully.")

        if "distance_km" not in notif_columns:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        ALTER TABLE notifications
                        ADD COLUMN distance_km FLOAT
                        """
                    )
                )

            print("distance_km column added successfully.")


except Exception as error:

    print("Database migration warning:", error)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="LifeLink AI",
    description="AI Blood Donor Management System",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,

    # allow_origins=["*"] so it works no matter which port
    # Live Server (or any local dev server) happens to use.
    allow_origins=["*"],

    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================================
# DATABASE DEPENDENCY
# =========================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "LifeLink AI Backend is Running",
        "status": "success"
    }


# =========================================================
# DONOR REGISTRATION
# =========================================================

@app.post("/donors")
def register_donor(
    donor_data: dict,
    db: Session = Depends(get_db)
):

    name = donor_data.get("name")
    age = donor_data.get("age")
    blood_group = donor_data.get("blood_group")
    phone = donor_data.get("phone")
    password = donor_data.get("password")
    city = donor_data.get("city")

    latitude = donor_data.get("latitude")
    longitude = donor_data.get("longitude")

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name is required"
        )

    if not age:
        raise HTTPException(
            status_code=400,
            detail="Age is required"
        )

    if not blood_group:
        raise HTTPException(
            status_code=400,
            detail="Blood group is required"
        )

    valid_blood_groups = [
        "A+",
        "A-",
        "B+",
        "B-",
        "AB+",
        "AB-",
        "O+",
        "O-"
    ]

    if blood_group not in valid_blood_groups:
       raise HTTPException(
        status_code=400,
        detail="Invalid blood group"
        )

    if not phone:
        raise HTTPException(
            status_code=400,
            detail="Phone number is required"
        )
    if not city:
        raise HTTPException(
            status_code=400,
            detail="City is required"
        )

    if not password:
        raise HTTPException(
            status_code=400,
            detail="Password is required"
        )


    # -----------------------------------------------------
    # CHECK DUPLICATE PHONE
    # -----------------------------------------------------

    existing_donor = (
        db.query(Donor)
        .filter(Donor.phone == phone)
        .first()
    )

    if existing_donor:

        raise HTTPException(
            status_code=409,
            detail="Donor with this phone number already exists"
        )


    # -----------------------------------------------------
    # CREATE DONOR
    # -----------------------------------------------------

    donor = Donor(

        name=name,

        age=int(age),

        blood_group=blood_group,

        phone=phone,

        password=password,

        city=city,

        available=True,

        latitude=float(latitude) if latitude not in (None, "") else None,

        longitude=float(longitude) if longitude not in (None, "") else None
    )


    db.add(donor)

    db.commit()

    db.refresh(donor)


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "message": "Donor registered successfully",

        "donor_id": donor.id,

        "name": donor.name,

        "blood_group": donor.blood_group,

        "phone": donor.phone,

        "city": donor.city,

        "available": donor.available,

        "latitude": donor.latitude,

        "longitude": donor.longitude
    }


# =========================================================
# DONOR LOGIN
# =========================================================

@app.post("/donor-login")
def donor_login(
    login_data: dict,
    db: Session = Depends(get_db)
):

    phone = login_data.get("phone")
    password = login_data.get("password")


    if not phone or not password:

        raise HTTPException(
            status_code=400,
            detail="Phone and password are required"
        )


    donor = (
        db.query(Donor)
        .filter(Donor.phone == phone)
        .first()
    )


    if not donor:

        raise HTTPException(
            status_code=401,
            detail="Invalid phone number or password"
        )


    if donor.password != password:

        raise HTTPException(
            status_code=401,
            detail="Invalid phone number or password"
        )


    return {

        "message": "Login successful",

        "donor_id": donor.id,

        "name": donor.name,

        "phone": donor.phone,

        "blood_group": donor.blood_group
    }


# =========================================================
# UPDATE DONOR LOCATION
# (call this after login/geolocation to keep GPS fresh)
# =========================================================

@app.put("/donors/{donor_id}/location")
def update_donor_location(
    donor_id: int,
    location_data: dict,
    db: Session = Depends(get_db)
):

    donor = (
        db.query(Donor)
        .filter(Donor.id == donor_id)
        .first()
    )

    if not donor:

        raise HTTPException(
            status_code=404,
            detail="Donor not found"
        )


    latitude = location_data.get("latitude")
    longitude = location_data.get("longitude")

    if latitude is None or longitude is None:

        raise HTTPException(
            status_code=400,
            detail="latitude and longitude are required"
        )


    donor.latitude = float(latitude)
    donor.longitude = float(longitude)

    db.commit()
    db.refresh(donor)


    return {

        "message": "Donor location updated successfully",

        "donor_id": donor.id,

        "latitude": donor.latitude,

        "longitude": donor.longitude
    }


# =========================================================
# GET DONOR
# =========================================================

@app.get("/donors/{donor_id}")
def get_donor(
    donor_id: int,
    db: Session = Depends(get_db)
):

    donor = (
        db.query(Donor)
        .filter(Donor.id == donor_id)
        .first()
    )


    if not donor:

        raise HTTPException(
            status_code=404,
            detail="Donor not found"
        )


    return {

        "id": donor.id,

        "name": donor.name,

        "age": donor.age,

        "blood_group": donor.blood_group,

        "phone": donor.phone,

        "city": donor.city,

        "available": donor.available,

        "latitude": donor.latitude,

        "longitude": donor.longitude
    }


# =========================================================
# GET ALL DONORS
# =========================================================

@app.get("/donors")
def get_all_donors(
    db: Session = Depends(get_db)
):

    donors = db.query(Donor).all()

    result = []


    for donor in donors:

        result.append({

            "id": donor.id,

            "name": donor.name,

            "age": donor.age,

            "blood_group": donor.blood_group,

            "phone": donor.phone,

            "city": donor.city,

            "available": donor.available,

            "latitude": donor.latitude,

            "longitude": donor.longitude
        })


    return {
        "donors": result
    }


# =========================================================
# GET DONOR NOTIFICATIONS
# =========================================================

@app.get("/donors/{donor_id}/notifications")
def get_notifications(
    donor_id: int,
    db: Session = Depends(get_db)
):

    donor = (
        db.query(Donor)
        .filter(Donor.id == donor_id)
        .first()
    )


    if not donor:

        raise HTTPException(
            status_code=404,
            detail="Donor not found"
        )


    notifications = (
        db.query(Notification)
        .filter(Notification.donor_id == donor_id)
        .order_by(desc(Notification.id))
        .all()
    )


    result = []


    for notification in notifications:
        blood_request = (
            db.query(BloodRequest)
            .filter(
                BloodRequest.id == notification.blood_request_id
            )
            .first()
        )

        result.append({

    "id":
        notification.id,

    "notification_id":
        notification.id,

    "blood_request_id":
        notification.blood_request_id,

    "blood_group":
        blood_request.blood_group,

    "units_required":
        blood_request.units_required,

    "city":
        blood_request.city,

    "request_type":
        blood_request.request_type,

    "alert_text":
        (
            "🚨 Emergency"
            if blood_request.request_type == "emergency"
            else "🩸 Blood Shortage"
        ),

    "priority_text":
        (
            "HIGH PRIORITY"
            if blood_request.request_type == "emergency"
            else "NORMAL PRIORITY"
        ),

    "message":
        notification.message,

    "match_score":
        notification.match_score,

    "match_rank":
        notification.match_rank,

    "distance_km":
        getattr(notification, "distance_km", None),

    "response":
        notification.response,

    "status":
        notification.status,

    "sent_at":
        notification.sent_at

})

    return {
        "notifications": result
    }


# =========================================================
# ACCEPT NOTIFICATION
# =========================================================

    # -----------------------------------------------------
    # FIND BLOOD REQUEST
    # -----------------------------------------------------
@app.post("/push-subscription")
def save_push_subscription(
    request_data: dict,
    db: Session = Depends(get_db)
):

    donor_id = request_data.get("donor_id")
    subscription = request_data.get("subscription")

    if not donor_id:
        raise HTTPException(
            status_code=400,
            detail="Donor ID is required"
        )

    if not subscription:
        raise HTTPException(
            status_code=400,
            detail="Push subscription is required"
        )

    endpoint = subscription.get("endpoint")
    keys = subscription.get("keys", {})
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")

    if not endpoint or not p256dh or not auth:
        raise HTTPException(
            status_code=400,
            detail="Invalid push subscription"
        )

    donor = (
        db.query(Donor)
        .filter(Donor.id == int(donor_id))
        .first()
    )

    if not donor:
        raise HTTPException(
            status_code=404,
            detail="Donor not found"
        )

    existing_subscription = (
        db.query(PushSubscription)
        .filter(PushSubscription.endpoint == endpoint)
        .first()
    )

    if existing_subscription:
        existing_subscription.donor_id = int(donor_id)
        existing_subscription.p256dh = p256dh
        existing_subscription.auth = auth
    else:
        new_subscription = PushSubscription(
            donor_id=int(donor_id),
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth
        )
        db.add(new_subscription)

    db.commit()

    return {
        "message": "Push subscription saved successfully"
    }


@app.put("/notifications/{notification_id}/accept")
def accept_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    if getattr(notification, "response", None) is not None:
        return {
            "message": "Donor has already responded",
            "response": notification.response
        }

    blood_request = (
        db.query(BloodRequest)
        .filter(BloodRequest.id == notification.blood_request_id)
        .first()
    )

    if not blood_request:
        raise HTTPException(
            status_code=404,
            detail="Blood request not found"
        )

    donor = (
        db.query(Donor)
        .filter(Donor.id == notification.donor_id)
        .first()
    )

    if not donor:
        raise HTTPException(
            status_code=404,
            detail="Donor not found"
        )

    if blood_request.status == "accepted":
        return {
            "message": "Another donor has already accepted this request",
            "status": "accepted"
        }

    notification.status = "accepted"
    notification.response = "accepted"
    blood_request.donor_id = donor.id
    blood_request.status = "accepted"
    donor.available = False

    other_notifications = (
        db.query(Notification)
        .filter(
            Notification.blood_request_id == blood_request.id,
            Notification.id != notification.id,
            Notification.status.in_(["pending", "sent"])
        )
        .all()
    )

    for other in other_notifications:
        other.status = "rejected"
        other.response = "rejected"

    db.commit()
    db.refresh(notification)

    return {
        "message": "Notification accepted successfully",
        "notification_id": notification.id,
        "status": notification.status,
        "response": notification.response,
        "donor_id": donor.id,
        "blood_request_id": blood_request.id
    }


@app.put("/notifications/{notification_id}/reject")
def reject_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    if getattr(notification, "response", None) is not None:
        return {
            "message": "Donor has already responded",
            "response": notification.response
        }

    notification.status = "rejected"
    notification.response = "rejected"

    db.commit()
    db.refresh(notification)

    return {
        "message": "Notification rejected successfully",
        "notification_id": notification.id,
        "status": notification.status,
        "response": notification.response
    }


@app.get("/blood-requests/{request_id}/responses")
def get_request_responses(
    request_id: int,
    db: Session = Depends(get_db)
):

    blood_request = (
        db.query(BloodRequest)
        .filter(BloodRequest.id == request_id)
        .first()
    )

    if not blood_request:
        raise HTTPException(
            status_code=404,
            detail="Blood request not found"
        )

    notifications = (
        db.query(Notification)
        .filter(Notification.blood_request_id == request_id)
        .all()
    )

    accepted = 0
    rejected = 0
    pending = 0

    for notification in notifications:
        response = getattr(notification, "response", None)
        if response == "accepted" or notification.status == "accepted":
            accepted += 1
        elif response == "rejected" or notification.status == "rejected":
            rejected += 1
        else:
            pending += 1

    return {
        "request_id": request_id,
        "blood_group": blood_request.blood_group,
        "request_type": blood_request.request_type,
        "units_required": blood_request.units_required,
        "accepted": accepted,
        "rejected": rejected,
        "pending": pending
    }


# =========================================================
# HOSPITAL SIGNUP
# =========================================================

@app.post("/hospital-signup")
def hospital_signup(
    hospital_data: dict,
    db: Session = Depends(get_db)
):

    name = hospital_data.get("name")
    email = hospital_data.get("email")
    password = hospital_data.get("password")
    confirm_password = hospital_data.get("confirm_password")

    phone = hospital_data.get("phone")
    city = hospital_data.get("city")
    address = hospital_data.get("address")

    latitude = hospital_data.get("latitude")
    longitude = hospital_data.get("longitude")

    # -----------------------------------------------------
    # REQUIRED FIELD VALIDATION
    # -----------------------------------------------------

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Hospital name is required"
        )

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Hospital email is required"
        )

    if not password:
        raise HTTPException(
            status_code=400,
            detail="Password is required"
        )

    if not confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Confirm password is required"
        )

    if password != confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters"
        )

    if not phone:
        raise HTTPException(
            status_code=400,
            detail="Phone number is required"
        )

    if not city:
        raise HTTPException(
            status_code=400,
            detail="City is required"
        )

    # -----------------------------------------------------
    # NORMALIZE EMAIL
    # -----------------------------------------------------

    email = email.strip().lower()

    # -----------------------------------------------------
    # CHECK DUPLICATE EMAIL
    # -----------------------------------------------------

    existing_hospital = (
        db.query(Hospital)
        .filter(Hospital.email == email)
        .first()
    )

    if existing_hospital:

        raise HTTPException(
            status_code=409,
            detail="Hospital with this email already exists"
        )

    # -----------------------------------------------------
    # HASH PASSWORD
    # -----------------------------------------------------

    hashed_password = hash_password(password)

    # -----------------------------------------------------
    # CREATE HOSPITAL
    # -----------------------------------------------------

    hospital = Hospital(
        name=name.strip(),
        email=email,
        password=hashed_password,
        phone=phone.strip() if phone else None,
        city=city.strip() if city else None,
        address=address.strip() if address else None,
        latitude=(
            float(latitude)
            if latitude not in (None, "")
            else None
        ),
        longitude=(
            float(longitude)
            if longitude not in (None, "")
            else None
        )
    )

    # -----------------------------------------------------
    # SAVE TO DATABASE
    # -----------------------------------------------------

    try:

        db.add(hospital)

        db.commit()

        db.refresh(hospital)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Hospital registration failed"
        )

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {
        "message": "Hospital registered successfully",
        "hospital_id": hospital.id,
        "name": hospital.name,
        "email": hospital.email,
        "phone": hospital.phone,
        "city": hospital.city,
        "latitude": hospital.latitude,
        "longitude": hospital.longitude
    }

# =========================================================
# HOSPITAL LOGIN
# =========================================================

@app.post("/hospital-login")
def hospital_login(
    login_data: dict,
    db: Session = Depends(get_db)
):

    identifier = login_data.get("identifier")
    password = login_data.get("password")

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not identifier:
        raise HTTPException(
            status_code=400,
            detail="Hospital ID or email is required"
        )

    if not password:
        raise HTTPException(
            status_code=400,
            detail="Password is required"
        )

    identifier = str(identifier).strip()

    # -----------------------------------------------------
    # FIND HOSPITAL
    # -----------------------------------------------------

    hospital = None

    # Try Hospital ID first
    try:

        hospital_id = int(identifier)

        hospital = (
            db.query(Hospital)
            .filter(Hospital.id == hospital_id)
            .first()
        )

    except ValueError:

        hospital = None

    # If ID was not found, try email
    if not hospital:

        hospital = (
            db.query(Hospital)
            .filter(
                Hospital.email == identifier.lower()
            )
            .first()
        )

    # -----------------------------------------------------
    # CHECK HOSPITAL
    # -----------------------------------------------------

    if not hospital:

        raise HTTPException(
            status_code=401,
            detail="Invalid Hospital ID/email or password"
        )

    # -----------------------------------------------------
    # VERIFY PASSWORD
    # -----------------------------------------------------

    if not hospital.password:

        raise HTTPException(
            status_code=401,
            detail="Hospital account is not configured for login"
        )

    if not verify_password(
        password,
        hospital.password
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid Hospital ID/email or password"
        )

    # -----------------------------------------------------
    # LOGIN SUCCESS
    # -----------------------------------------------------

    return {
        "message": "Hospital login successful",
        "hospital_id": hospital.id,
        "name": hospital.name,
        "email": hospital.email,
        "phone": hospital.phone,
        "city": hospital.city,
        "address": hospital.address,
        "latitude": hospital.latitude,
        "longitude": hospital.longitude
    }

# =========================================================
# CREATE HOSPITAL
# =========================================================

@app.post("/hospitals")
def create_hospital(
    hospital_data: dict,
    db: Session = Depends(get_db)
):

    name = hospital_data.get("name")
    phone = hospital_data.get("phone")
    city = hospital_data.get("city")
    address = hospital_data.get("address")
    available_blood_groups = hospital_data.get("available_blood_groups")
    latitude = hospital_data.get("latitude")
    longitude = hospital_data.get("longitude")


    if not name:
        raise HTTPException(
            status_code=400,
            detail="Hospital name is required"
        )


    hospital = Hospital(

        name=name,

        phone=phone,

        city=city,

        address=address,

        available_blood_groups=available_blood_groups,

        latitude=float(latitude) if latitude not in (None, "") else None,

        longitude=float(longitude) if longitude not in (None, "") else None
    )


    db.add(hospital)

    db.commit()

    db.refresh(hospital)


    return {

        "message": "Hospital created successfully",

        "hospital_id": hospital.id,

        "latitude": hospital.latitude,

        "longitude": hospital.longitude
    }


# =========================================================
# UPDATE HOSPITAL LOCATION
# (used by the "Update My Location" button on the dashboard)
# =========================================================

@app.put("/hospitals/{hospital_id}/location")
def update_hospital_location(
    hospital_id: int,
    location_data: dict,
    db: Session = Depends(get_db)
):

    hospital = (
        db.query(Hospital)
        .filter(Hospital.id == hospital_id)
        .first()
    )

    if not hospital:

        raise HTTPException(
            status_code=404,
            detail="Hospital not found"
        )


    latitude = location_data.get("latitude")
    longitude = location_data.get("longitude")

    if latitude is None or longitude is None:

        raise HTTPException(
            status_code=400,
            detail="latitude and longitude are required"
        )


    hospital.latitude = float(latitude)
    hospital.longitude = float(longitude)

    db.commit()
    db.refresh(hospital)


    return {

        "message": "Hospital location updated successfully",

        "hospital_id": hospital.id,

        "latitude": hospital.latitude,

        "longitude": hospital.longitude
    }


# =========================================================
# CREATE BLOOD REQUEST
# Matches donors by blood group + GPS radius (falls back to
# city text match if lat/long is missing for hospital or donor)
# =========================================================

@app.post("/blood-requests")
def create_blood_request(
    request_data: dict,
    db: Session = Depends(get_db)
):

    hospital_id = request_data.get("hospital_id")
    blood_group = request_data.get("blood_group")
    units_required = request_data.get("units_required")
    city = request_data.get("city")
    request_type = request_data.get("request_type", "emergency")

    if request_type not in ["emergency", "shortage"]:
        raise HTTPException(
            status_code=400,
            detail="request_type must be 'emergency' or 'shortage'"
        )

    if request_type == "emergency":
        radius_km = 30
        priority = "high"
        alert_text = "🚨 Emergency"
    else:
        radius_km = 20
        priority = "normal"
        alert_text = "🩸 Blood Shortage"

    priority_text = (
        "HIGH PRIORITY"
        if priority == "high"
        else "NORMAL PRIORITY"
    )

    if not hospital_id:
        raise HTTPException(status_code=400, detail="Hospital ID is required")

    if not blood_group:
        raise HTTPException(status_code=400, detail="Blood group is required")

    valid_blood_groups = [
        "A+",
        "A-",
         "B+",
         "B-",
        "AB+",
        "AB-",
         "O+",
          "O-"
    ]

    if blood_group not in valid_blood_groups:
       raise HTTPException(
        status_code=400,
        detail="Invalid blood group"
       )
    if not units_required:
        raise HTTPException(status_code=400, detail="Units required is required")

    if not city:
        raise HTTPException(status_code=400, detail="City is required")

    hospital = (
        db.query(Hospital)
        .filter(Hospital.id == int(hospital_id))
        .first()
    )

    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    blood_request = BloodRequest(
        hospital_id=int(hospital_id),
        blood_group=blood_group,
        units_required=int(units_required),
        city=city,
        request_type=request_type,
        status="pending"
    )

    db.add(blood_request)
    db.commit()
    db.refresh(blood_request)
    candidate_donors = (
        db.query(Donor)
        .filter(
            Donor.blood_group == blood_group,
            Donor.available == True
        )
        .all()
    )
    print("================================")
    print("BLOOD REQUEST:", blood_group)
    print("CITY:", city)
    print("CANDIDATE DONORS:")

    for d in candidate_donors:
        print(
            "Donor ID:", d.id,
            "| Name:", d.name,
            "| Blood:", d.blood_group,
            "| Available:", d.available,
            "| City:", d.city,
            "| Lat:", d.latitude,
            "| Lon:", d.longitude
        )

    print("================================")

    hospital_has_gps = (
        hospital.latitude is not None
        and hospital.longitude is not None
    )

    scored_donors = []

    for donor in candidate_donors:
        distance_km = None
        donor_has_gps = (
            donor.latitude is not None
            and donor.longitude is not None
        )

        if hospital_has_gps and donor_has_gps:
            distance_km = calculate_distance(
                hospital.latitude,
                hospital.longitude,
                donor.latitude,
                donor.longitude
            )

            if distance_km > radius_km:
                continue
        else:
            if donor.city and city:
                if donor.city.strip().lower() != city.strip().lower():
                    continue

        accepted, rejected = get_donor_accept_reject_counts(
            db, donor.id
        )

        score = calculate_match_score(
            distance_km,
            radius_km,
            donor.age,
            accepted,
            rejected
        )

        scored_donors.append({
            "donor": donor,
            "distance_km": distance_km,
            "score": score
        })

    scored_donors.sort(
        key=lambda entry: entry["score"],
        reverse=True
    )

    notification_count = 0
    matched_donors = []

    for rank, entry in enumerate(scored_donors, start=1):
        donor = entry["donor"]
        distance_km = entry["distance_km"]
        score = entry["score"]
        if distance_km is not None:
            message = (
                f"{alert_text}: "
                f"{blood_group} blood required "
                f"at {hospital.name} (~{round(distance_km, 1)} km away)"
            )
        else:
            message = (
                f"{alert_text}: "
                f"{blood_group} blood required "
                f"at {hospital.name}"
            )

        notification = Notification(
            donor_id=donor.id,
            blood_request_id=blood_request.id,
            message=message,
            sent_at=datetime.utcnow(),
            status="pending",
            match_score=score,
            match_rank=rank,
            distance_km=distance_km
        )

        # -----------------------------------------------------
        # PUSH NOTIFICATION
        # -----------------------------------------------------
        # The database notification is the source of truth.
        # A browser push subscription is optional.
        # If push delivery is unavailable, keep the notification
        # as pending so the donor can still see it in the app.
        # -----------------------------------------------------

        try:
            push_subscription = (
                db.query(PushSubscription)
                .filter(PushSubscription.donor_id == donor.id)
                .first()
            )

            if push_subscription:
                subscription_info = {
                    "endpoint": push_subscription.endpoint,
                    "keys": {
                        "p256dh": push_subscription.p256dh,
                        "auth": push_subscription.auth
                    }
                }

                push_sent = send_push_notification(
                    subscription_info,
                    "🚨 LifeLink AI Blood Request",
                    message
                )

                if push_sent:
                    notification.status = "sent"
                    print(
                        f"Push notification sent to donor {donor.id}"
                    )
                else:
                    # Push failed, but the notification is still valid.
                    notification.status = "pending"
                    print(
                        f"Push failed for donor {donor.id}. "
                        f"Keeping notification as pending."
                    )

            else:
                # No browser subscription. The donor can still see the
                # notification from the application dashboard.
                notification.status = "pending"
                print(
                    f"No push subscription found for donor {donor.id}. "
                    f"Notification saved as pending."
                )

        except Exception as error:
            # Push service errors must not make the blood-request
            # notification unusable. Keep it pending.
            notification.status = "pending"
            print(
                f"Push notification failed for donor {donor.id}: {error}. "
                f"Keeping notification as pending."
            )

        # Save the database notification regardless of push result.
        db.add(notification)
        db.commit()
        notification_count += 1

        matched_donors.append({
            "donor_id": donor.id,
            "name": donor.name,
            "rank": rank,
            "match_score": score,
            "distance_km": (
                round(distance_km, 1)
                if distance_km is not None
                else None
            )
        })

    db.commit()

    return {
        "message": "Blood request created successfully",
        "request_id": blood_request.id,
        "hospital_id": hospital.id,
        "hospital_name": hospital.name,
        "blood_group": blood_group,
        "units_required": int(units_required),
        "city": city,
        "request_type": request_type,
        "priority": priority,
        "match_radius_km": radius_km,
        "matching_donors": len(candidate_donors),
        "notifications_sent": notification_count,
        "matched_donors": matched_donors,
        "status": blood_request.status
    }


# =========================================================
# GET HOSPITAL BLOOD REQUESTS
# =========================================================

@app.get("/hospitals/{hospital_id}/blood-requests")
def get_hospital_requests(
    hospital_id: int,
    db: Session = Depends(get_db)
):

    hospital = (
        db.query(Hospital)
        .filter(
            Hospital.id == hospital_id
        )
        .first()
    )


    if not hospital:

        raise HTTPException(
            status_code=404,
            detail="Hospital not found"
        )


    requests = (

        db.query(BloodRequest)

        .filter(
            BloodRequest.hospital_id ==
            hospital_id
        )

        .order_by(
            desc(BloodRequest.id)
        )

        .all()
    )


    result = []


    for request in requests:

        accepted_donor = None


        if request.donor_id:

            donor = (

                db.query(Donor)

                .filter(
                    Donor.id ==
                    request.donor_id
                )

                .first()
            )


            if donor:

                accepted_donor = {

                    "id":
                        donor.id,

                    "name":
                        donor.name,

                    "blood_group":
                        donor.blood_group,

                    "phone":
                        donor.phone,

                    "city":
                        donor.city
                }


        result.append({

            "request_id":
                request.id,

            "blood_group":
                request.blood_group,

            "units_required":
                request.units_required,

            "city":
                request.city,

            "request_type":
                request.request_type,

            "status":
                request.status,

            "accepted_donor":
                accepted_donor
        })


    return {

        "hospital_id":
            hospital_id,

        "hospital_name":
            hospital.name,

        "blood_requests":
            result
    }


# =========================================================
# GET ALL HOSPITALS
# =========================================================

@app.get("/hospitals")
def get_all_hospitals(
    db: Session = Depends(get_db)
):

    hospitals = db.query(Hospital).all()

    result = []


    for hospital in hospitals:

        result.append({

            "id":
                hospital.id,

            "name":
                hospital.name,

            "phone":
                hospital.phone,

            "city":
                hospital.city,

            "address":
                hospital.address,

            "available_blood_groups":
                hospital.available_blood_groups,

            "latitude":
                hospital.latitude,

            "longitude":
                hospital.longitude
        })


    return {
        "hospitals": result
    }