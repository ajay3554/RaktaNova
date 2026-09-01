const DONOR_API_URL = "http://127.0.0.1:8000";
const DONOR_VAPID_PUBLIC_KEY =
    "BATkLbDGETZD-IlWwmdQhrDkSRTmShmgGoMV2IeroAKc2DHEinkXRue4XrUiK0Oc7bUqho3NllLlqy2Plz0rCwE";

let donorPageLatitude = null;
let donorPageLongitude = null;

function setMessage(id, text, isError = false) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    el.style.color = isError ? "#d62839" : "#198754";
}

function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/-/g, "+")
        .replace(/_/g, "/");

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }

    return outputArray;
}

async function registerDonorServiceWorker() {
    if (!("serviceWorker" in navigator)) return null;

    try {
        return await navigator.serviceWorker.register(
            "/frontend/service-worker.js"
        );
    } catch (error) {
        console.error("Service worker registration failed:", error);
        return null;
    }
}

async function subscribeDonorPush(donorId) {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
        return false;
    }

    if (!("Notification" in window)) return false;

    if (Notification.permission !== "granted") return false;

    try {
        const registration = await navigator.serviceWorker.ready;

        let subscription =
            await registration.pushManager.getSubscription();

        if (!subscription) {
            subscription =
                await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey:
                        urlBase64ToUint8Array(
                            DONOR_VAPID_PUBLIC_KEY
                        )
                });
        }

        const response = await fetch(
            `${DONOR_API_URL}/push-subscription`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    donor_id: donorId,
                    subscription: subscription.toJSON()
                })
            }
        );

        return response.ok;
    } catch (error) {
        console.error("Push subscription failed:", error);
        return false;
    }
}

function captureDonorLocation() {
    const statusEl =
        document.getElementById("donor-location-status");

    if (!navigator.geolocation) {
        if (statusEl) {
            statusEl.textContent =
                "❌ Geolocation is not supported by this browser.";
        }
        return;
    }

    if (statusEl) {
        statusEl.textContent =
            "📍 Fetching your current location...";
    }

    navigator.geolocation.getCurrentPosition(
        function(position) {
            donorPageLatitude = position.coords.latitude;
            donorPageLongitude = position.coords.longitude;

            if (statusEl) {
                statusEl.textContent =
                    `✅ Location captured (${donorPageLatitude.toFixed(4)}, ${donorPageLongitude.toFixed(4)})`;
            }
        },
        function(error) {
            console.error(error);
            if (statusEl) {
                statusEl.textContent =
                    "⚠️ Location permission was not granted. You can still register.";
            }
        },
        {
            enableHighAccuracy: true,
            timeout: 10000
        }
    );
}

async function registerDonorPage() {
    const name =
        document.getElementById("donor-name")?.value.trim();
    const age =
        document.getElementById("donor-age")?.value;
    const bloodGroup =
        document.getElementById("donor-blood-group")?.value;
    const phone =
        document.getElementById("donor-phone")?.value.trim();
    const password =
        document.getElementById("donor-password")?.value;
    const city =
        document.getElementById("donor-city")?.value.trim();

    if (!name || !age || !bloodGroup || !phone || !password || !city) {
        setMessage(
            "donor-signup-message",
            "Please fill all fields.",
            true
        );
        return;
    }

    if (password.length < 4) {
        setMessage(
            "donor-signup-message",
            "Password must contain at least 4 characters.",
            true
        );
        return;
    }

    try {
        const response = await fetch(
            `${DONOR_API_URL}/donors`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: name,
                    age: Number(age),
                    blood_group: bloodGroup,
                    phone: phone,
                    password: password,
                    city: city,
                    available: true,
                    latitude: donorPageLatitude,
                    longitude: donorPageLongitude
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Donor registration failed."
            );
        }

        localStorage.setItem("donorId", data.donor_id);
        localStorage.setItem("donorName", data.name || name);
        localStorage.setItem("donorBloodGroup", data.blood_group || bloodGroup);
        localStorage.setItem("donorPhone", data.phone || phone);
        localStorage.setItem("donorCity", data.city || city);

        setMessage(
            "donor-signup-message",
            `Registration successful! Donor ID: ${data.donor_id}. Redirecting to login...`
        );

        setTimeout(function() {
            window.location.href = "donor-login.html";
        }, 1200);

    } catch (error) {
        console.error("Donor registration error:", error);
        setMessage(
            "donor-signup-message",
            error.message,
            true
        );
    }
}

async function donorLoginPage() {
    const phone =
        document.getElementById("donor-login-phone")?.value.trim();
    const password =
        document.getElementById("donor-login-password")?.value;

    if (!phone || !password) {
        setMessage(
            "donor-login-message",
            "Please enter phone number and password.",
            true
        );
        return;
    }

    try {
        const response = await fetch(
            `${DONOR_API_URL}/donor-login`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    phone: phone,
                    password: password
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Donor login failed."
            );
        }

        localStorage.setItem("donorId", data.donor_id);
        localStorage.setItem("donorName", data.name || "Donor");
        localStorage.setItem("donorPhone", data.phone || phone);
        localStorage.setItem(
            "donorBloodGroup",
            data.blood_group || "-"
        );

        await registerDonorServiceWorker();

        if ("Notification" in window &&
            Notification.permission === "default") {
            try {
                await Notification.requestPermission();
            } catch (error) {
                console.error(error);
            }
        }

        await subscribeDonorPush(data.donor_id);

        setMessage(
            "donor-login-message",
            "Login successful. Opening donor dashboard..."
        );

        setTimeout(function() {
            window.location.href = "donor.html";
        }, 700);

    } catch (error) {
        console.error("Donor login error:", error);
        setMessage(
            "donor-login-message",
            error.message,
            true
        );
    }
}

async function loadDonorProfilePage() {
    const donorId = localStorage.getItem("donorId");

    if (!donorId) {
        window.location.href = "donor-login.html";
        return;
    }

    try {
        const response = await fetch(
            `${DONOR_API_URL}/donors/${donorId}`,
            { cache: "no-store" }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Failed to load donor profile."
            );
        }

        localStorage.setItem("donorName", data.name || "Donor");
        localStorage.setItem("donorPhone", data.phone || "-");
        localStorage.setItem(
            "donorBloodGroup",
            data.blood_group || "-"
        );
        localStorage.setItem("donorCity", data.city || "-");

        const welcome =
            document.getElementById("donor-welcome");
        const subtitle =
            document.getElementById("donor-profile-subtitle");

        if (welcome) {
            welcome.textContent =
                `Welcome, ${data.name || "Donor"}`;
        }

        if (subtitle) {
            subtitle.textContent =
                `${data.blood_group || "-"} blood group • ${data.city || "-"}`;
        }

        document.getElementById("donor-display-id").textContent =
            data.id ?? donorId;
        document.getElementById("donor-display-blood").textContent =
            data.blood_group || "-";
        document.getElementById("donor-display-phone").textContent =
            data.phone || "-";
        document.getElementById("donor-display-city").textContent =
            data.city || "-";

        const locationStatus =
            document.getElementById("donor-dashboard-location");

        if (locationStatus) {
            if (data.latitude != null && data.longitude != null) {
                locationStatus.textContent =
                    `✅ Location available for donor matching`;
            } else {
                locationStatus.textContent =
                    "📍 Location not set yet. Update it for better nearby matching.";
            }
        }

    } catch (error) {
        console.error(error);
        const locationStatus =
            document.getElementById("donor-dashboard-location");

        if (locationStatus) {
            locationStatus.textContent =
                `⚠️ ${error.message}`;
        }
    }
}

function updateDonorLocationPage() {
    const donorId = localStorage.getItem("donorId");
    const statusEl =
        document.getElementById("donor-dashboard-location");

    if (!donorId) {
        window.location.href = "donor-login.html";
        return;
    }

    if (!navigator.geolocation) {
        if (statusEl) {
            statusEl.textContent =
                "❌ Geolocation is not supported.";
        }
        return;
    }

    if (statusEl) {
        statusEl.textContent =
            "📍 Getting your current location...";
    }

    navigator.geolocation.getCurrentPosition(
        async function(position) {
            try {
                const response = await fetch(
                    `${DONOR_API_URL}/donors/${donorId}/location`,
                    {
                        method: "PUT",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude
                        })
                    }
                );

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.detail ||
                        "Failed to update location."
                    );
                }

                if (statusEl) {
                    statusEl.textContent =
                        "✅ Your location was updated successfully.";
                }
            } catch (error) {
                console.error(error);
                if (statusEl) {
                    statusEl.textContent =
                        `❌ ${error.message}`;
                }
            }
        },
        function(error) {
            console.error(error);
            if (statusEl) {
                statusEl.textContent =
                    "⚠️ Could not get your location.";
            }
        },
        {
            enableHighAccuracy: true,
            timeout: 10000
        }
    );
}

async function enableDonorPushPage() {
    const donorId = localStorage.getItem("donorId");

    if (!donorId) {
        window.location.href = "donor-login.html";
        return;
    }

    if (!("Notification" in window)) {
        alert("Browser notifications are not supported.");
        return;
    }

    try {
        const permission =
            await Notification.requestPermission();

        if (permission !== "granted") {
            alert("Notification permission was not granted.");
            return;
        }

        await registerDonorServiceWorker();

        const saved =
            await subscribeDonorPush(donorId);

        if (saved) {
            alert("🔔 Donor notifications enabled successfully!");
        } else {
            alert("⚠️ Notification subscription could not be saved.");
        }
    } catch (error) {
        console.error(error);
        alert(error.message);
    }
}

async function loadDonorNotificationsPage() {
    const donorId = localStorage.getItem("donorId");
    const container =
        document.getElementById("donor-notifications");

    if (!donorId) {
        window.location.href = "donor-login.html";
        return;
    }

    container.innerHTML =
        '<div class="empty-state">⏳ Loading blood requests...</div>';

    try {
        const response = await fetch(
            `${DONOR_API_URL}/donors/${donorId}/notifications`,
            { cache: "no-store" }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Failed to load notifications."
            );
        }

        renderDonorNotificationsPage(data.notifications || []);

    } catch (error) {
        console.error(error);
        container.innerHTML =
            `<div class="empty-state">❌ ${error.message}</div>`;
    }
}

function renderDonorNotificationsPage(notifications) {
    const container =
        document.getElementById("donor-notifications");

    container.innerHTML = "";

    if (!notifications.length) {
        container.innerHTML =
            '<div class="empty-state">📭 No blood requests found right now.</div>';
        return;
    }

    notifications.forEach(function(notification) {
        const card =
            document.createElement("div");

        card.className = "notification-card";
        card.id =
            `donor-notification-${notification.id}`;

        const responseState =
            notification.response || notification.status || "pending";

        let responseText = "";
        let actions = "";

        if (responseState === "accepted") {
            responseText =
                '<p>✅ You accepted this blood request.</p>';
        } else if (responseState === "rejected") {
            responseText =
                '<p>❌ You rejected this blood request.</p>';
        } else {
            responseText =
                '<p>⏳ Waiting for your response.</p>';

            actions = `
                <div class="notification-actions">
                    <button type="button"
                        onclick="acceptDonorNotificationPage(${notification.id})">
                        ✅ Accept
                    </button>
                    <button type="button"
                        class="secondary"
                        onclick="rejectDonorNotificationPage(${notification.id})">
                        ❌ Reject
                    </button>
                </div>
            `;
        }

        card.innerHTML = `
            <h3>🩸 ${notification.blood_group || "Blood"} Blood Request</h3>
            <p>${notification.message || "A hospital is requesting blood."}</p>

            <div class="notification-meta">
                <div>
                    <strong>Units</strong><br>
                    ${notification.units_required ?? "-"}
                </div>
                <div>
                    <strong>City</strong><br>
                    ${notification.city || "-"}
                </div>
                <div>
                    <strong>Request Type</strong><br>
                    ${notification.request_type || "-"}
                </div>
                <div>
                    <strong>Match Score</strong><br>
                    ${notification.match_score ?? "N/A"}
                </div>
                <div>
                    <strong>Match Rank</strong><br>
                    ${notification.match_rank ?? "N/A"}
                </div>
                <div>
                    <strong>Approx. Distance</strong><br>
                    ${notification.distance_km != null
                        ? Number(notification.distance_km).toFixed(2) + " km"
                        : "N/A"}
                </div>
            </div>

            ${responseText}
            ${actions}
        `;

        container.appendChild(card);
    });
}

async function acceptDonorNotificationPage(notificationId) {
    await respondToDonorNotificationPage(
        notificationId,
        "accept"
    );
}

async function rejectDonorNotificationPage(notificationId) {
    await respondToDonorNotificationPage(
        notificationId,
        "reject"
    );
}

async function respondToDonorNotificationPage(
    notificationId,
    action
) {
    try {
        const response = await fetch(
            `${DONOR_API_URL}/notifications/${notificationId}/${action}`,
            {
                method: "PUT"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                `Failed to ${action} notification.`
            );
        }

        alert(
            data.message ||
            `Notification ${action}ed successfully.`
        );

        await loadDonorNotificationsPage();

    } catch (error) {
        console.error(error);
        alert(error.message);
    }
}

function donorLogoutPage() {
    localStorage.removeItem("donorId");
    localStorage.removeItem("donorName");
    localStorage.removeItem("donorPhone");
    localStorage.removeItem("donorBloodGroup");
    localStorage.removeItem("donorCity");

    window.location.href = "donor-login.html";
}

document.addEventListener("DOMContentLoaded", function() {
    if (document.getElementById("donor-welcome")) {
        registerDonorServiceWorker();
        loadDonorProfilePage();
    }
});
