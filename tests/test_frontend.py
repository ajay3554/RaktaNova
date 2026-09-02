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

    # Current UI button = "Sign in"
    page.get_by_role(
        "button",
        name=re.compile(
            r"Sign in",
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

    # Current UI button = "Sign in to workspace"
    page.get_by_role(
        "button",
        name=re.compile(
            r"Sign in",
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
    assert "RaktaNova" in page.title()

    # Main heading
    heading = page.locator("h1")

    assert heading.is_visible()

    assert (
        "Connecting Life Through Blood Donation"
        in heading.inner_text()
    )

    # Current homepage uses links,
    # not buttons.

    donor_link = page.get_by_role(
        "link",
        name=re.compile(
            r"Donor Access",
            re.IGNORECASE
        )
    )

    assert donor_link.is_visible()

    hospital_link = page.get_by_role(
        "link",
        name=re.compile(
            r"Hospital Portal",
            re.IGNORECASE
        )
    )

    assert hospital_link.is_visible()


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

    # Donor welcome heading
    assert page.locator(
        "#donor-welcome"
    ).is_visible()

    # Body exists
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

    # Current UI button =
    # "Refresh requests"
    notification_button = page.get_by_role(
        "button",
        name=re.compile(
            r"Refresh requests",
            re.IGNORECASE
        )
    )

    assert notification_button.is_visible()

    notification_button.click()

    page.wait_for_timeout(
        1000
    )

    # Notification container
    notification_container = page.locator(
        "#donor-notifications"
    )

    assert notification_container.is_visible()


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

    # Units
    page.locator(
        "#units-required"
    ).fill("1")

    # City
    page.locator(
        "#city"
    ).fill("chennai")

    # Blood group
    page.locator(
        "#blood-group"
    ).select_option("O+")

    # Request type
    page.locator(
        "#request-type"
    ).select_option("emergency")

    # Current UI button =
    # "Send blood request"
    create_button = page.get_by_role(
        "button",
        name=re.compile(
            r"Send blood request",
            re.IGNORECASE
        )
    )

    assert create_button.is_visible()

    create_button.click()

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

    # Current UI button =
    # "View blood requests"
    view_requests_button = page.get_by_role(
        "button",
        name=re.compile(
            r"View blood requests",
            re.IGNORECASE
        )
    )

    assert view_requests_button.is_visible()

    view_requests_button.click()

    page.wait_for_timeout(
        1000
    )

    requests_container = page.locator(
        "#hospital-requests"
    )

    assert requests_container.is_visible()


# =========================================================
# DONOR DASHBOARD
# =========================================================

def test_donor_dashboard(page: Page):

    phone, password, _ = (
        register_test_donor()
    )

    login_as_donor(
        page,
        phone,
        password
    )

    # Welcome heading
    welcome = page.locator(
        "#donor-welcome"
    )

    assert welcome.is_visible()

    # Notifications section
    notifications = page.locator(
        "#donor-notifications"
    )

    assert notifications.is_visible()

    # Refresh requests button
    refresh_button = page.get_by_role(
        "button",
        name=re.compile(
            r"Refresh requests",
            re.IGNORECASE
        )
    )

    assert refresh_button.is_visible()


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

    # Name
    page.locator(
        "#donor-name"
    ).fill(
        "Test Donor"
    )

    # Age
    page.locator(
        "#donor-age"
    ).fill(
        "25"
    )

    # Phone
    page.locator(
        "#donor-phone"
    ).fill(
        unique_phone
    )

    # Password
    page.locator(
        "#donor-password"
    ).fill(
        "Test@123"
    )

    # City
    page.locator(
        "#donor-city"
    ).fill(
        "Chennai"
    )

    # Blood group
    page.locator(
        "#donor-blood-group"
    ).select_option(
        "O+"
    )

    # Current UI button =
    # "Create donor account"
    register_button = page.get_by_role(
        "button",
        name=re.compile(
            r"Create donor account",
            re.IGNORECASE
        )
    )

    assert register_button.is_visible()

    register_button.click()

    # Registration should redirect
    # to donor login page.
    page.wait_for_url(
        re.compile(
            r"donor-login\.html"
        ),
        timeout=10000
    )

    # Verify donor login page loaded
    assert page.locator(
        "#donor-login-phone"
    ).is_visible()

    assert page.locator(
        "#donor-login-password"
    ).is_visible()

    assert page.get_by_role(
        "button",
        name=re.compile(
            r"Sign in",
            re.IGNORECASE
        )
    ).is_visible()