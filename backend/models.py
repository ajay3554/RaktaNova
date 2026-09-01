from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean, DateTime
from backend.database import Base


class Donor(Base):
    __tablename__ = "donors"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    age = Column(Integer)

    blood_group = Column(String(10), nullable=False)

    phone = Column(String(20), unique=True, nullable=False, index=True)

    password = Column(String(255), nullable=False)

    city = Column(String(100))

    available = Column(Boolean, default=True)

    latitude = Column(Float, nullable=True)

    longitude = Column(Float, nullable=True)

class PushSubscription(Base):

    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    donor_id = Column(
        Integer,
        ForeignKey("donors.id"),
        nullable=False
    )

    endpoint = Column(
        String,
        nullable=False
    )

    p256dh = Column(
        String,
        nullable=False
    )

    auth = Column(
        String,
        nullable=False
    )

class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    email = Column(
        String(150),
        unique=True,
        nullable=False,
        index=True
    )

    password = Column(
        String(255),
        nullable=False
    )

    phone = Column(String(20))

    city = Column(String(100))

    address = Column(String)

    available_blood_groups = Column(String)

    latitude = Column(Float, nullable=True)

    longitude = Column(Float, nullable=True)


class BloodRequest(Base):
    __tablename__ = "blood_requests"

    id = Column(Integer, primary_key=True, index=True)

    donor_id = Column(Integer, nullable=True)

    hospital_id = Column(Integer, nullable=False)

    blood_group = Column(String(10), nullable=False)

    units_required = Column(Integer, nullable=False)

    city = Column(String(100))

    status = Column(String(20), default="pending")
    response = Column(String(20), nullable=True)
    match_score = Column(Float, nullable=True)

    request_type = Column(String(20), default="emergency")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    donor_id = Column(Integer, nullable=False)

    blood_request_id = Column(Integer, nullable=False)

    message = Column(String, nullable=False)

    sent_at = Column(DateTime, nullable=True)

    status = Column(String(20), default="pending")

    # AI ranking: 0-100 score combining GPS distance,
    # donor reliability history, and age suitability
    match_score = Column(Float, nullable=True)

    match_rank = Column(Integer, nullable=True)
    response = Column(String(20), nullable=True)
    distance_km = Column(Float, nullable=True)