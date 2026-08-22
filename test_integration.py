import httpx


BASE_URL = "http://127.0.0.1:8000"


def test_complete_blood_request_flow():

    # Step 1: Create blood request
    request_data = {
        "hospital_id": 1,
        "blood_group": "O+",
        "units_required": 1,
        "city": "chennai"
    }

    create_response = httpx.post(
        f"{BASE_URL}/blood-requests",
        json=request_data
    )

    assert create_response.status_code == 200

    request_result = create_response.json()

    assert "request_id" in request_result

    request_id = request_result["request_id"]

    # Step 2: Get hospital blood requests
    requests_response = httpx.get(
        f"{BASE_URL}/hospitals/1/blood-requests"
    )

    assert requests_response.status_code == 200

    requests_result = requests_response.json()

    assert "blood_requests" in requests_result

    # Step 3: Verify created request exists
    blood_requests = requests_result["blood_requests"]

    assert any(
        request.get("request_id") == request_id
        for request in blood_requests
    )


def test_donor_notification_flow():

    # Step 1: Get donor notifications
    notifications_response = httpx.get(
        f"{BASE_URL}/donors/18/notifications"
    )

    assert notifications_response.status_code == 200

    notifications_result = notifications_response.json()

    assert "notifications" in notifications_result

    notifications = notifications_result["notifications"]

    assert len(notifications) > 0

    # Step 2: Get notification ID
    notification_id = notifications[0]["notification_id"]

    # Step 3: Accept notification
    accept_response = httpx.put(
        f"{BASE_URL}/notifications/{notification_id}/accept"
    )

    assert accept_response.status_code == 200

    result = accept_response.json()

    assert result["status"] == "accepted"
    assert result["response"] == "accepted"