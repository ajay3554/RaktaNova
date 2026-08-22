import httpx
import time
BASE_URL = "http://127.0.0.1:8000"


def test_backend_is_running():
    response = httpx.get(f"{BASE_URL}/")

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

    assert isinstance(result["blood_requests"], list)

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
def test_accept_notification():

    notifications_response = httpx.get(
        f"{BASE_URL}/donors/18/notifications"
    )

    assert notifications_response.status_code == 200

    notifications = notifications_response.json()["notifications"]

    assert len(notifications) > 0

    notification_id = notifications[0]["notification_id"]

    response = httpx.put(
        f"{BASE_URL}/notifications/{notification_id}/accept"
    )

    assert response.status_code == 200

    result = response.json()

    assert result["status"] == "accepted"
    assert result["response"] == "accepted"
def test_reject_notification():

    # Create a fresh blood request
    data = {
        "hospital_id": 1,
        "blood_group": "O+",
        "units_required": 1,
        "city": "chennai"
    }

    create_response = httpx.post(
        f"{BASE_URL}/blood-requests",
        json=data
    )

    assert create_response.status_code == 200

    # Get donor notifications
    notifications_response = httpx.get(
        f"{BASE_URL}/donors/18/notifications"
    )

    assert notifications_response.status_code == 200

    notifications = notifications_response.json()["notifications"]

    assert len(notifications) > 0

    # Get the newest notification
    notification_id = notifications[0]["notification_id"]

    # Reject notification
    response = httpx.put(
        f"{BASE_URL}/notifications/{notification_id}/reject"
    )

    assert response.status_code == 200

    result = response.json()

    assert result["status"] == "rejected"
    assert result["response"] == "rejected"

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
def test_register_donor():

    unique_phone = f"9{int(time.time())}"[-10:]

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