import re
import time

import httpx

from playwright.sync_api import Page


FRONTEND_URL = "http://127.0.0.1:5500/frontend"
API_URL = "http://127.0.0.1:8000"


# =========================================================
# HELPERS
# =========================================================

def register_test_donor():
    """
    Register a fresh donor and return:
    (phone, password, donor_id)
    """

    phone = "9" + str(time.time_ns())[-9:]
    password = "test123"

    response = httpx.post(
        f"{API_URL}/donors",
        json={
            "name": "Automation Test Donor",
            "age": 25,
            "blood_group": "O+",
            "phone": phone,
            "password": password,
            "city": "chennai",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "donor_id" in data

    return phone, password, data["donor_id"]


def register_test_hospital():
    """
    Register a fresh hospital and return:
    (email, password, hospital_id)
    """

    unique = str(time.time_ns())[-9:]

    email = f"testhospital{unique}@example.com"
    password = "test1234"

    response = httpx.post(
        f"{API_URL}/hospital-signup",
        json={
            "name": "Automation Test Hospital",
            "email": email,
            "password": password,
            "confirm_password": password,
            "phone": "9" + unique,
            "city": "chennai",
            "address": "123 Test Street",
            "available_blood_groups": "O+, A+",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "hospital_id" in data

    return email, password, data["hospital_id"]


def login_as_donor(
    page: Page,
    phone: str,
    password: str
):
    """
    Login using the real donor login page.
    """

    page.goto(
        f"{FRONTEND_URL}/donor-login.html"
    )

    page.wait_for_load_state(
        "networkidle"
    )

    page.locator(
        "#donor-login-phone"
    ).fill(phone)

    page.locator(
        "#donor-login-password"
    ).fill(password)

    page.get_by_role(
        "button",
        name=re.compile(
            r"Login",
            re.IGNORECASE
        )
    ).click()

    page.wait_for_url(
        re.compile(
            r"donor\.html"
        ),
        timeout=10000
    )

    page.wait_for_load_state(
        "networkidle"
    )


def login_as_hospital(
    page: Page,
    email: str,
    password: str
):
    """
    Login using the real hospital login page.
    """

    page.goto(
        f"{FRONTEND_URL}/hospital-login.html"
    )

    page.wait_for_load_state(
        "networkidle"
    )

    page.locator(
        "#hospital-login-identifier"
    ).fill(email)

    page.locator(
        "#hospital-login-password"
    ).fill(password)

    page.get_by_role(
        "button",
        name=re.compile(
            r"Login",
            re.IGNORECASE
        )
    ).click()

    page.wait_for_url(
        re.compile(
            r"hospital\.html"
        ),
        timeout=10000
    )

    page.wait_for_load_state(
        "networkidle"
    )


# =========================================================
# HOMEPAGE
# =========================================================

def test_RaktaNova_homepage(page: Page):

    page.goto(
        f"{FRONTEND_URL}/index.html"
    )

    page.wait_for_load_state(
        "networkidle"
    )

    # Website title
    assert page.title() == "RaktaNova"

    # Main heading
    heading = page.locator("h1")

    assert heading.is_visible()

    assert (
        "Save Lives with RaktaNova"
        in heading.inner_text()
    )

    # Donor button
    donor_button = page.get_by_role(
        "button",
        name="🩸 I'm a Donor"
    )

    assert donor_button.is_visible()

    # Hospital button
    hospital_button = page.get_by_role(
        "button",
        name="🏥 I'm a Hospital"
    )

    assert hospital_button.is_visible()


# =========================================================
# DONOR LOGIN
# =========================================================

def test_donor_login(page: Page):

    page.on(
        "dialog",
        lambda dialog: dialog.accept()
    )

    phone, password, _ = (
        register_test_donor()
    )

    login_as_donor(
        page,
        phone,
        password
    )

    assert page.locator(
        "#donor-welcome"
    ).is_visible()

    assert page.locator(
        "body"
    ).is_visible()


# =========================================================
# DONOR NOTIFICATIONS
# =========================================================

def test_donor_notifications(page: Page):

    page.on(
        "dialog",
        lambda dialog: dialog.accept()
    )

    phone, password, donor_id = (
        register_test_donor()
    )

    # Create matching blood request
    response = httpx.post(
        f"{API_URL}/blood-requests",
        json={
            "hospital_id": 1,
            "blood_group": "O+",
            "units_required": 1,
            "city": "chennai",
        },
    )

    assert response.status_code == 200

    login_as_donor(
        page,
        phone,
        password
    )

    notification_button = page.get_by_role(
        "button",
        name=re.compile(
            r"View Notifications",
            re.IGNORECASE
        )
    )

    assert notification_button.is_visible()

    notification_button.click()

    page.wait_for_timeout(
        1500
    )

    body_text = page.locator(
        "#donor-notifications"
    ).inner_text()

    assert body_text.strip() != ""


# =========================================================
# HOSPITAL CREATE BLOOD REQUEST
# =========================================================

def test_create_blood_request(page: Page):

    page.on(
        "dialog",
        lambda dialog: dialog.accept()
    )

    email, password, hospital_id = (
        register_test_hospital()
    )

    login_as_hospital(
        page,
        email,
        password
    )

    # Hospital ID is automatically loaded
    assert page.locator(
        "#hospital-id"
    ).input_value() == str(
        hospital_id
    )

    page.locator(
        "#units-required"
    ).fill("1")

    page.locator(
        "#city"
    ).fill("chennai")

    page.locator(
        "#blood-group"
    ).select_option("O+")

    page.locator(
        "#request-type"
    ).select_option("emergency")

    page.get_by_role(
        "button",
        name=re.compile(
            r"Create Blood Request",
            re.IGNORECASE
        )
    ).click()

    page.wait_for_timeout(
        1500
    )

    body_text = page.locator(
        "#hospital-requests"
    ).inner_text()

    assert "O+" in body_text
    assert "Blood Request" in body_text

    assert "Units:" in body_text
    assert "1" in body_text

    assert "City:" in body_text
    assert "chennai" in body_text

    assert "Request Type:" in body_text
    assert "emergency" in body_text

    assert "Status:" in body_text
    assert "pending" in body_text


# =========================================================
# HOSPITAL VIEW REQUESTS
# =========================================================

def test_hospital_view_requests(page: Page):

    email, password, _ = (
        register_test_hospital()
    )

    login_as_hospital(
        page,
        email,
        password
    )

    view_requests_button = page.get_by_role(
        "button",
        name=re.compile(
            r"View Requests",
            re.IGNORECASE
        )
    )

    assert view_requests_button.is_visible()

    view_requests_button.click()

    page.wait_for_timeout(
        1000
    )

    body_text = page.locator(
        "body"
    ).inner_text()

    assert (
        "Hospital Blood Requests"
        in body_text
    )

    assert (
        "View your blood requests and their current status."
        in body_text
    )


# =========================================================
# DONOR RESPONSE STATUS
# =========================================================

def test_donor_response_status(page: Page):

    email, password, _ = (
        register_test_hospital()
    )

    login_as_hospital(
        page,
        email,
        password
    )

    body_text = page.locator(
        "body"
    ).inner_text()

    assert (
        "Donor Response Status"
        in body_text
    )

    assert (
        "Select a blood request to view donor responses."
        in body_text
    )


# =========================================================
# DONOR REGISTRATION
# =========================================================

def test_donor_registration(page: Page):

    page.goto(
        f"{FRONTEND_URL}/donor-signup.html"
    )

    page.wait_for_load_state(
        "networkidle"
    )

    unique_phone = (
        "9" +
        str(time.time_ns())[-9:]
    )

    page.locator(
        "#donor-name"
    ).fill(
        "Test Donor"
    )

    page.locator(
        "#donor-age"
    ).fill(
        "25"
    )

    page.locator(
        "#donor-phone"
    ).fill(
        unique_phone
    )

    page.locator(
        "#donor-password"
    ).fill(
        "Test@123"
    )

    page.locator(
        "#donor-city"
    ).fill(
        "Chennai"
    )

    page.locator(
        "#donor-blood-group"
    ).select_option(
        "O+"
    )

    page.get_by_role(
        "button",
        name=re.compile(
            r"Register as Donor",
            re.IGNORECASE
        )
    ).click()

    page.wait_for_url(
        re.compile(
            r"donor-login\.html"
        ),
        timeout=10000
    )

    body_text = page.locator(
        "body"
    ).inner_text()

    assert "Donor" in body_text