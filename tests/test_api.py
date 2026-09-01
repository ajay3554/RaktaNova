import httpx
import time


BASE_URL = "http://127.0.0.1:8000"


def register_test_donor():
    """
    Create a fresh donor for notification testing.
    Returns donor_id.
    """

    unique_phone = "9" + str(time.time_ns())[-9:]

    data = {
        "name": "Automation Test Donor",
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

    assert result["message"] == "Donor registered successfully"
    assert result["blood_group"] == "O+"
    assert result["phone"] == unique_phone
    assert result["available"] is True

    # Backend response should contain donor_id
    assert "donor_id" in result

    return result["donor_id"]


def create_blood_request():
    """
    Create a fresh O+ blood request.
    Returns request_id.
    """

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


def get_pending_notification(donor_id, retries=10, delay=0.5):
    """
    Wait for notification creation and return
    the first pending notification.
    """

    for _ in range(retries):

        response = httpx.get(
            f"{BASE_URL}/donors/{donor_id}/notifications"
        )

        assert response.status_code == 200

        result = response.json()

        assert "notifications" in result

        notifications = result["notifications"]

        pending_notifications = [
            notification
            for notification in notifications
            if notification.get("status") in ["pending", "sent"]
            and notification.get("response") is None
            and "notification_id" in notification
        ]

        if pending_notifications:
            return pending_notifications[0]

        time.sleep(delay)

    print("ALL NOTIFICATIONS:", notifications)

    return None


# =========================================================
# BASIC API TESTS
# =========================================================

def test_backend_is_running():

    response = httpx.get(
        f"{BASE_URL}/"
    )

    assert response.status_code == 200


def test_create_blood_request():

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


def test_get_blood_requests():

    response = httpx.get(
        f"{BASE_URL}/hospitals/1/blood-requests"
    )

    assert response.status_code == 200

    result = response.json()

    assert "hospital_id" in result
    assert "hospital_name" in result
    assert "blood_requests" in result

    assert isinstance(
        result["blood_requests"],
        list
    )


def test_create_blood_request_invalid_data():

    data = {
        "hospital_id": 1,
        "blood_group": "INVALID",
        "units_required": 1,
        "city": "chennai"
    }

    response = httpx.post(
        f"{BASE_URL}/blood-requests",
        json=data
    )

    assert response.status_code != 200


# =========================================================
# ACCEPT NOTIFICATION TEST
# =========================================================

def test_accept_notification():

    # Step 1: Create fresh donor
    donor_id = register_test_donor()

    # Step 2: Create fresh blood request
    create_blood_request()

    # Step 3: Wait for pending notification
    notification = get_pending_notification(
        donor_id
    )

    assert notification is not None

    notification_id = notification["notification_id"]

    # Step 4: Accept notification
    response = httpx.put(
        f"{BASE_URL}/notifications/{notification_id}/accept"
    )

    assert response.status_code == 200

    result = response.json()

    print("ACCEPT API RESPONSE:", result)

    assert "status" in result
    assert "response" in result

    assert result["status"] == "accepted"
    assert result["response"] == "accepted"


# =========================================================
# REJECT NOTIFICATION TEST
# =========================================================

def test_reject_notification():

    # Step 1: Create a completely fresh donor
    donor_id = register_test_donor()

    # Step 2: Create fresh blood request
    create_blood_request()

    # Step 3: Wait for pending notification
    notification = get_pending_notification(
        donor_id
    )

    assert notification is not None

    notification_id = notification["notification_id"]

    # Step 4: Reject notification
    response = httpx.put(
        f"{BASE_URL}/notifications/{notification_id}/reject"
    )

    assert response.status_code == 200

    result = response.json()

    print("REJECT API RESPONSE:", result)

    assert "status" in result
    assert "response" in result

    assert result["status"] == "rejected"
    assert result["response"] == "rejected"


# =========================================================
# NOT FOUND TESTS
# =========================================================

def test_donor_not_found():

    response = httpx.get(
        f"{BASE_URL}/donors/99999"
    )

    assert response.status_code == 404


def test_hospital_not_found():

    response = httpx.get(
        f"{BASE_URL}/hospitals/99999/blood-requests"
    )

    assert response.status_code == 404


def test_notification_not_found():

    response = httpx.put(
        f"{BASE_URL}/notifications/99999/accept"
    )

    assert response.status_code == 404


# =========================================================
# DONOR REGISTRATION TEST
# =========================================================

def test_register_donor():

    unique_phone = "9" + str(time.time_ns())[-9:]

    data = {
        "name": "Test Donor Automation",
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

    assert result["message"] == "Donor registered successfully"
    assert result["blood_group"] == "O+"
    assert result["phone"] == unique_phone
    assert result["available"] is True