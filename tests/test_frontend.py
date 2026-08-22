from playwright.sync_api import Page


def test_lifelink_homepage(page: Page):
    page.goto("http://127.0.0.1:5500/frontend/index.html")
    page.wait_for_load_state("networkidle")

    assert page.title() is not None


def test_donor_login(page: Page):
    page.on("dialog", lambda dialog: dialog.accept())

    page.goto("http://127.0.0.1:5500/frontend/index.html")

    page.locator("#login-phone").fill("9876501234")

    page.get_by_role(
        "button",
        name="Login",
        exact=True
    ).click()

    page.wait_for_timeout(1000)


def test_donor_notifications(page: Page):
    page.on("dialog", lambda dialog: dialog.accept())

    page.goto("http://127.0.0.1:5500/frontend/index.html")

    page.locator("#login-phone").fill("9876501234")

    page.get_by_role(
        "button",
        name="Login",
        exact=True
    ).click()

    page.wait_for_timeout(1000)

    page.get_by_role(
        "button",
        name="View Notifications",
        exact=True
    ).click()

    page.wait_for_timeout(1000)

    body_text = page.locator("body").inner_text()

    assert "Emergency" in body_text


def test_create_blood_request(page: Page):
    page.on("dialog", lambda dialog: dialog.accept())

    page.goto("http://127.0.0.1:5500/frontend/index.html")
    page.wait_for_load_state("networkidle")

    # Hospital ID
    page.locator("#hospital-id").fill("1")

    # Units Required
    page.locator("#units-required").fill("1")

    # City
    page.locator("#city").fill("chennai")

    # Blood Group
    page.locator("#blood-group").select_option("O+")

    # Request Type
    page.locator("#request-type").select_option("emergency")

    # Create Blood Request
    page.get_by_role(
        "button",
        name="Create Blood Request",
        exact=True
    ).click()

    page.wait_for_timeout(1500)

    body_text = page.locator("body").inner_text()

    assert "O+ Blood Request" in body_text
    assert "Units: 1" in body_text
    assert "City: chennai" in body_text
    assert "Request Type: emergency" in body_text
    assert "Status: pending" in body_text


def test_hospital_view_requests(page: Page):
    page.goto("http://127.0.0.1:5500/frontend/index.html")
    page.wait_for_load_state("networkidle")

    # Find View Requests button
    view_requests_button = page.get_by_role(
        "button",
        name="View Requests",
        exact=True
    )

    assert view_requests_button.is_visible()

    # Click View Requests
    view_requests_button.click()

    page.wait_for_timeout(1000)

    body_text = page.locator("body").inner_text()

    assert "Hospital Blood Requests" in body_text
    assert "View blood requests and accepted donors." in body_text


def test_donor_response_status(page: Page):
    page.goto("http://127.0.0.1:5500/frontend/index.html")
    page.wait_for_load_state("networkidle")

    body_text = page.locator("body").inner_text()

    assert "Donor Response Status" in body_text
    assert "Select a blood request to view donor responses." in body_text


def test_donor_registration(page: Page):
    page.goto("http://127.0.0.1:5500/frontend/index.html")
    page.wait_for_load_state("networkidle")

    # Donor Name
    page.locator("#donor-name").fill("Test Donor")

    # Age
    page.locator("#donor-age").fill("25")

    # Phone
    page.locator("#donor-phone").fill("9876543210")

    # Password
    page.locator("#donor-password").fill("Test@123")

    # City
    page.locator("#donor-city").fill("Chennai")

    # Blood Group
    page.locator("#donor-blood-group").select_option("O+")

    # Register button
    page.get_by_role(
        "button",
        name="Register as Donor",
        exact=True
    ).click()

    page.wait_for_timeout(1500)

    body_text = page.locator("body").inner_text()

    assert "Donor" in body_text