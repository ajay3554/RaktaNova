import httpx
import time


BASE_URL = "http://127.0.0.1:8000"


# =========================================================
# HELPER: REGISTER FRESH DONOR
# =========================================================

def register_test_donor():

    unique_phone = (
        "9" + str(time.time_ns())[-9:]
    )

    data = {
        "name": "Integration Test Donor",
        "age": 25,
        "blood_group": "O+",
        "phone": unique_phone,
        "password": "test123",
        "city": "chennai"
    }

    response = httpx.post(
        f"{BASE_URL}/donors",
        json=data
    )

    assert response.status_code == 200

    result = response.json()

    assert "donor_id" in result

    assert result["blood_group"] == "O+"

    assert result["phone"] == unique_phone

    assert result["available"] is True

    return result["donor_id"]


# =========================================================
# HELPER: CREATE BLOOD REQUEST
# =========================================================

def create_blood_request():

    data = {
        "hospital_id": 1,
        "blood_group": "O+",
        "units_required": 1,
        "city": "chennai"
    }

    response = httpx.post(
        f"{BASE_URL}/blood-requests",
        json=data
    )

    assert response.status_code == 200

    result = response.json()

    assert "request_id" in result

    return result["request_id"]


# =========================================================
# HELPER: GET PENDING NOTIFICATION
# =========================================================

def get_pending_notification(
    donor_id,
    retries=10,
    delay=0.5
):

    notifications = []

    for attempt in range(retries):

        response = httpx.get(
            f"{BASE_URL}/donors/{donor_id}/notifications"
        )

        assert response.status_code == 200

        result = response.json()

        assert "notifications" in result

        notifications = result["notifications"]

        print(
            f"Attempt {attempt + 1}: "
            f"{notifications}"
        )

        pending_notifications = [
            notification
            for notification in notifications
            if notification.get("status")
            in ["pending", "sent"]
            and notification.get("response") is None
            and notification.get("notification_id")
            is not None
        ]

        if pending_notifications:

            return pending_notifications[0]

        time.sleep(delay)

    print(
        "ALL NOTIFICATIONS:",
        notifications
    )

    return None


# =========================================================
# TEST 1
# COMPLETE BLOOD REQUEST FLOW
# =========================================================

def test_complete_blood_request_flow():

    donor_id = register_test_donor()

    request_id = create_blood_request()

    response = httpx.get(
        f"{BASE_URL}/hospitals/1/blood-requests"
    )

    assert response.status_code == 200

    result = response.json()

    assert "blood_requests" in result

    blood_requests = result["blood_requests"]

    assert any(
        request.get("request_id") == request_id
        for request in blood_requests
    )


# =========================================================
# TEST 2
# ACCEPT NOTIFICATION FLOW
# =========================================================

def test_donor_notification_accept_flow():

    # Create fresh donor
    donor_id = register_test_donor()

    # Create fresh blood request
    create_blood_request()

    # Wait for notification
    notification = get_pending_notification(
        donor_id
    )

    assert notification is not None

    notification_id = (
        notification["notification_id"]
    )

    print(
        "ACCEPTING NOTIFICATION:",
        notification_id
    )

    # Accept notification
    response = httpx.put(
        f"{BASE_URL}/notifications/"
        f"{notification_id}/accept"
    )

    assert response.status_code == 200

    result = response.json()

    print(
        "ACCEPT RESPONSE:",
        result
    )

    assert result["status"] == "accepted"

    assert result["response"] == "accepted"


# =========================================================
# TEST 3
# REJECT NOTIFICATION FLOW
# =========================================================

def test_donor_notification_reject_flow():

    # Create fresh donor
    donor_id = register_test_donor()

    # Create fresh blood request
    create_blood_request()

    # Wait for notification
    notification = get_pending_notification(
        donor_id
    )

    assert notification is not None

    notification_id = (
        notification["notification_id"]
    )

    print(
        "REJECTING NOTIFICATION:",
        notification_id
    )

    # Reject notification
    response = httpx.put(
        f"{BASE_URL}/notifications/"
        f"{notification_id}/reject"
    )

    assert response.status_code == 200

    result = response.json()

    print(
        "REJECT RESPONSE:",
        result
    )

    assert result["status"] == "rejected"

    assert result["response"] == "rejected"