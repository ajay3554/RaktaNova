console.log("SCRIPT LOADED");


const API_URL = "http://127.0.0.1:8000";


// Holds GPS captured for the donor registration form
let donorLatitude = null;
let donorLongitude = null;


async function registerServiceWorker() {

    if (!("serviceWorker" in navigator)) {

        console.log(
            "Service Worker is not supported."
        );

        return;
    }

    try {

        const registration =
            await navigator.serviceWorker.register(
                "/frontend/service-worker.js"
            );

        console.log(
            "Service Worker registered:",
            registration
        );

    }
    catch (error) {

        console.error(
            "Service Worker registration failed:",
            error
        );

    }
}


// =====================================================
// VAPID PUBLIC KEY CONVERTER
// =====================================================

function urlBase64ToUint8Array(base64String) {

    const padding =
        "=".repeat(
            (4 - base64String.length % 4) % 4
        );

    const base64 =
        (base64String + padding)
            .replace(/-/g, "+")
            .replace(/_/g, "/");

    const rawData =
        window.atob(base64);

    const outputArray =
        new Uint8Array(
            rawData.length
        );

    for (
        let i = 0;
        i < rawData.length;
        ++i
    ) {

        outputArray[i] =
            rawData.charCodeAt(i);
    }

    return outputArray;
}


// Register service worker when script loads
registerServiceWorker();


// =====================================================
// PUSH NOTIFICATION SUBSCRIPTION
// =====================================================

async function subscribeToPushNotifications(donorId) {

    if (!("serviceWorker" in navigator)) {

        console.log(
            "Service Worker not supported."
        );

        return;
    }


    if (!("PushManager" in window)) {

        console.log(
            "Push notifications not supported."
        );

        return;
    }


    if (Notification.permission !== "granted") {

        console.log(
            "Notification permission not granted."
        );

        return;
    }


    try {

        const registration =
            await navigator.serviceWorker.ready;


        let subscription =
            await registration.pushManager.getSubscription();


        if (!subscription) {

            subscription =
                await registration.pushManager.subscribe({

                    userVisibleOnly: true,

                    applicationServerKey:
                        urlBase64ToUint8Array(
                            "BATkLbDGETZD-IlWwmdQhrDkSRTmShmgGoMV2IeroAKc2DHEinkXRue4XrUiK0Oc7bUqho3NllLlqy2Plz0rCwE"
                        )

                });

        }


        console.log(
            "Push subscription created:",
            subscription
        );


        const response =
            await fetch(
                `${API_URL}/push-subscription`,
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        donor_id:
                            donorId,

                        subscription:
                            subscription.toJSON()

                    })

                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            console.error(
                "Failed to save subscription:",
                result
            );

            return;
        }


        console.log(
            "Push subscription saved:",
            result
        );

    }
    catch (error) {

        console.error(
            "Push subscription failed:",
            error
        );

    }
}


// =====================================================
// SHOW DONOR
// =====================================================

function showDonor() {

    document
        .getElementById("donor-register")
        .scrollIntoView({
            behavior: "smooth"
        });
}


// =====================================================
// SHOW HOSPITAL
// =====================================================

function showHospital() {

    document
        .getElementById("hospital")
        .scrollIntoView({
            behavior: "smooth"
        });
}


// =====================================================
// CAPTURE DONOR GPS LOCATION
// =====================================================

function captureDonorLocation() {

    const statusEl =
        document.getElementById(
            "donor-location-status"
        );


    if (!navigator.geolocation) {

        statusEl.textContent =
            "❌ Geolocation not supported by this browser.";

        return;
    }


    statusEl.textContent =
        "📍 Fetching your location...";


    navigator.geolocation.getCurrentPosition(

        function(position) {

            donorLatitude =
                position.coords.latitude;

            donorLongitude =
                position.coords.longitude;


            statusEl.textContent =
                `✅ Location captured (${donorLatitude.toFixed(4)}, ${donorLongitude.toFixed(4)})`;

        },

        function(error) {

            console.error(error);

            statusEl.textContent =
                "⚠️ Could not get location. You can still register — matching will fall back to city name.";

        }

    );
}


// =====================================================
// REGISTER DONOR
// =====================================================

async function registerDonor() {

    const name =
        document.getElementById(
            "donor-name"
        ).value.trim();


    const age =
        document.getElementById(
            "donor-age"
        ).value;


    const bloodGroup =
        document.getElementById(
            "donor-blood-group"
        ).value;


    const phone =
        document.getElementById(
            "donor-phone"
        ).value.trim();


    const password =
        document.getElementById(
            "donor-password"
        ).value;


    const city =
        document.getElementById(
            "donor-city"
        ).value.trim();


    if (
        !name ||
        !age ||
        !bloodGroup ||
        !phone ||
        !password ||
        !city
    ) {

        alert(
            "Please fill all fields."
        );

        return;
    }


    if (password.length < 4) {

        alert(
            "Password must contain at least 4 characters."
        );

        return;
    }


    try {

        const response =
            await fetch(
                `${API_URL}/donors`,
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        name:
                            name,

                        age:
                            Number(age),

                        blood_group:
                            bloodGroup,

                        phone:
                            phone,

                        password:
                            password,

                        city:
                            city,

                        available:
                            true,

                        latitude:
                            donorLatitude,

                        longitude:
                            donorLongitude

                    })

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Donor registration failed"
            );
        }


        console.log(
            "Donor Registration:",
            data
        );


        alert(
            `Registration successful!\nDonor ID: ${data.donor_id}`
        );


        document.getElementById(
            "donor-name"
        ).value = "";


        document.getElementById(
            "donor-age"
        ).value = "";


        document.getElementById(
            "donor-blood-group"
        ).value = "";


        document.getElementById(
            "donor-phone"
        ).value = "";


        document.getElementById(
            "donor-password"
        ).value = "";


        document.getElementById(
            "donor-city"
        ).value = "";


        donorLatitude = null;
        donorLongitude = null;


        document.getElementById(
            "donor-location-status"
        ).textContent =
            "📍 Location not captured yet";


        document.getElementById(
            "donor-login"
        ).scrollIntoView({
            behavior: "smooth"
        });

    }

    catch (error) {

        console.error(error);

        alert(
            error.message
        );

    }
}


// =====================================================
// DONOR LOGIN
// =====================================================

async function donorLogin() {

    const phone =
        document.getElementById(
            "login-phone"
        ).value.trim();


    const password =
        document.getElementById(
            "login-password"
        ).value;


    if (!phone || !password) {

        alert(
            "Please enter phone and password."
        );

        return;
    }


    try {

        const response =
            await fetch(
                `${API_URL}/donor-login`,
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        phone:
                            phone,

                        password:
                            password

                    })

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Login failed"
            );
        }


        // SAVE DONOR ID

        localStorage.setItem(
            "donorId",
            data.donor_id
        );


        alert(
            "Login successful!"
        );


        // CREATE AND SAVE PUSH SUBSCRIPTION

        await subscribeToPushNotifications(
            data.donor_id
        );


        document
            .getElementById("donor")
            .scrollIntoView({
                behavior: "smooth"
            });

    }

    catch (error) {

        console.error(error);

        alert(
            error.message
        );

    }

}
// =====================================================
// GET DONOR NOTIFICATIONS
// =====================================================

async function getNotifications() {

    const donorId =
        localStorage.getItem(
            "donorId"
        );


    if (!donorId) {

        alert(
            "Please login first."
        );

        return;
    }


    try {

        const response =
            await fetch(
                `${API_URL}/donors/${donorId}/notifications`,
                {
                    cache: "no-store"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to load notifications"
            );
        }


        const container =
            document.getElementById(
                "donor-notifications"
            );


        container.innerHTML = "";


        if (
            !data.notifications ||
            data.notifications.length === 0
        ) {

            container.innerHTML = `
                <div class="card">
                    <p>
                        📭 No blood requests found.
                    </p>
                </div>
            `;

            return;
        }


        data.notifications.forEach(
            function(notification) {
                if (
                  notification.response === "accepted" ||
                  notification.response === "rejected"
                ) {
                    return;
                }

                const card =
                    document.createElement(
                        "div"
                    );


                card.className =
                    "card notification-card";
                
                card.id =
                   `notification-${notification.id}`;


                const status =
                    notification.status ||
                    "pending";


                const statusText =
                    status.toUpperCase();


                card.innerHTML = `

                    <h3>
                        ${notification.alert_text ||
                        "🩸 Blood Request"}
                    </h3>

                    <p>
                        <strong>
                            Blood Group:
                        </strong>
                        ${notification.blood_group || "-"}
                    </p>

                    <p>
                        <strong>
                            Units Required:
                        </strong>
                        ${notification.units_required || "-"}
                    </p>

                    <p>
                        <strong>
                            City:
                        </strong>
                        ${notification.city || "-"}
                    </p>

                    <p>
                        <strong>
                            Priority:
                        </strong>
                        ${notification.priority_text || "-"}
                    </p>

                    <p>
                        <strong>
                            Distance:
                        </strong>
                        ${
                            notification.distance_km != null
                                ? Number(
                                    notification.distance_km
                                  ).toFixed(2) + " km"
                                : "Not available"
                        }
                    </p>

                    <p>
                        <strong>
                            Match Score:
                        </strong>
                        ${
                            notification.match_score != null
                                ? Number(
                                    notification.match_score
                                  ).toFixed(2)
                                : "N/A"
                        }
                    </p>

                    <p>
                        <strong>
                            Status:
                        </strong>
                        ${statusText}
                    </p>

                    ${
                        status === "pending" || status === "sent"
                            ? `
                                <button
                                    onclick="acceptNotification(${notification.id})"
                                >
                                    ✅ Accept
                                </button>

                                <button
                                    onclick="rejectNotification(${notification.id})"
                                >
                                    ❌ Reject
                                </button>
                              `
                            : ""
                    }

                `;


                container.appendChild(
                    card
                );

            }
        );

    }

    catch (error) {

        console.error(error);

        alert(
            error.message
        );

    }
}


// =====================================================
// ACCEPT NOTIFICATION
// =====================================================

async function acceptNotification(
    notificationId
) {

    try {

        const response =
            await fetch(
                `${API_URL}/notifications/${notificationId}/accept`,
                {

                    method: "PUT"

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to accept notification"
            );
        }


        alert(
            data.message ||
            "Notification accepted successfully!"
        );
        const card =
            document.getElementById(
              `notification-${notificationId}`
        );

        if (card) {
           card.remove();
        }

    }
    catch (error) {

        console.error(error);

        alert(
            error.message
        );

    }
}


// =====================================================
// REJECT NOTIFICATION
// =====================================================

async function rejectNotification(
    notificationId
) {

    try {

        const response =
            await fetch(
                `${API_URL}/notifications/${notificationId}/reject`,
                {

                    method: "PUT"

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to reject notification"
            );
        }


        alert(
            data.message ||
            "Notification rejected successfully!"
        );


        const card =
             document.getElementById(
              `notification-${notificationId}`
        );

        if (card) {
            card.remove();
        }

    }

    catch (error) {

        console.error(error);

        alert(
            error.message
        );

    }
}


// =====================================================
// UPDATE HOSPITAL LOCATION
// =====================================================

function updateHospitalLocation() {

    const hospitalId =
        document.getElementById(
            "hospital-id"
        ).value;


    const statusEl =
        document.getElementById(
            "hospital-location-status"
        );


    if (!hospitalId) {

        alert(
            "Please enter Hospital ID first."
        );

        return;
    }


    if (!navigator.geolocation) {

        statusEl.textContent =
            "❌ Geolocation not supported.";

        return;
    }


    statusEl.textContent =
        "📍 Getting hospital location...";


    navigator.geolocation.getCurrentPosition(

        async function(position) {

            const latitude =
                position.coords.latitude;


            const longitude =
                position.coords.longitude;


            try {

                const response =
                    await fetch(
                        `${API_URL}/hospitals/${hospitalId}/location`,
                        {

                            method: "PUT",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({

                                latitude:
                                    latitude,

                                longitude:
                                    longitude

                            })

                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.detail ||
                        "Failed to update hospital location"
                    );
                }


                statusEl.textContent =
                    `✅ Hospital location updated (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`;


                alert(
                    "Hospital location updated successfully!"
                );

            }

            catch (error) {

                console.error(error);

                statusEl.textContent =
                    "❌ Failed to update location.";

                alert(
                    error.message
                );

            }

        },

        function(error) {

            console.error(error);

            statusEl.textContent =
                "⚠️ Could not get hospital location.";

        }

    );
}


// =====================================================
// CREATE BLOOD REQUEST
// =====================================================

async function createBloodRequest() {

    const hospitalId =
        document.getElementById(
            "hospital-id"
        ).value;


    const bloodGroup =
        document.getElementById(
            "blood-group"
        ).value;


    const unitsRequired =
        document.getElementById(
            "units-required"
        ).value;


    const requestType =
        document.getElementById(
            "request-type"
        ).value;


    const city =
        document.getElementById(
            "city"
        ).value.trim();


    if (
        !hospitalId ||
        !bloodGroup ||
        !unitsRequired ||
        !requestType ||
        !city
    ) {

        alert(
            "Please fill all blood request fields."
        );

        return;
    }


    try {

        const response =
            await fetch(
                `${API_URL}/blood-requests`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        hospital_id:
                            Number(hospitalId),

                        blood_group:
                            bloodGroup,

                        units_required:
                            Number(unitsRequired),

                        city:
                            city,

                        request_type:
                            requestType

                    })

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to create blood request"
            );
        }


        alert(
            data.message ||
            "Blood request created successfully!"
        );


        document.getElementById(
            "units-required"
        ).value = "";


        await getHospitalRequests();

    }

    catch (error) {

        console.error(error);

        alert(
            error.message
        );

    }
}


// =====================================================
// GET HOSPITAL REQUESTS
// =====================================================

async function getHospitalRequests() {

    const hospitalId =
        document.getElementById(
            "hospital-id"
        ).value;


    if (!hospitalId) {

        alert(
            "Please enter Hospital ID first."
        );

        return;
    }


    try {

        const response =
            await fetch(
                `${API_URL}/hospitals/${hospitalId}/blood-requests`
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to load hospital requests"
            );
        }


        const container =
            document.getElementById(
                "hospital-requests"
            );


        container.innerHTML = "";


        if (
            !data.blood_requests ||
            data.blood_requests.length === 0
        ) {

            container.innerHTML = `
                <div class="card">
                    <p>
                        📭 No blood requests found.
                    </p>
                </div>
            `;

            return;
        }


        data.blood_requests.forEach(
            function(request) {

                const card =
                    document.createElement(
                        "div"
                    );


                card.className =
                    "card notification-card";
                card.id= `notification-${request.id}`;


                card.innerHTML = `

                    <h3>
                        🩸
                        ${request.blood_group}
                        Blood Request
                    </h3>

                    <p>
                        <strong>
                            Units:
                        </strong>
                        ${request.units_required}
                    </p>

                    <p>
                        <strong>
                            City:
                        </strong>
                        ${request.city}
                    </p>

                    <p>
                        <strong>
                            Request Type:
                        </strong>
                        ${request.request_type}
                    </p>

                    <p>
                        <strong>
                            Status:
                        </strong>
                        ${request.status}
                    </p>

                `;


                container.appendChild(
                    card
                );

            }
        );

    }

    catch (error) {

        console.error(error);

        alert(
            error.message
        );

    }
}
// =====================================================
// LOGOUT DONOR
// =====================================================

function donorLogout() {

    localStorage.removeItem(
        "donorId"
    );

    alert(
        "Logged out successfully."
    );

    window.location.reload();
}


// =====================================================
// CHECK DONOR LOGIN
// =====================================================

function checkDonorLogin() {

    const donorId =
        localStorage.getItem(
            "donorId"
        );


    if (!donorId) {

        console.log(
            "No donor logged in."
        );

        return false;
    }


    console.log(
        "Logged-in donor ID:",
        donorId
    );

    return true;
}


// =====================================================
// PAGE LOAD
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        console.log(
            "LifeLink AI loaded successfully."
        );


        const donorId =
            localStorage.getItem(
                "donorId"
            );


        if (donorId) {

            console.log(
                "Existing donor session:",
                donorId
            );

        }

    }
);


// =====================================================
// AUTO REFRESH DONOR NOTIFICATIONS
// =====================================================

async function refreshDonorNotifications() {

    const donorId =
        localStorage.getItem(
            "donorId"
        );


    if (!donorId) {
        return;
    }


    const donorSection =
        document.getElementById(
            "donor"
        );


    if (!donorSection) {
        return;
    }


    try {

        await getNotifications();

    }

    catch (error) {

        console.error(
            "Notification refresh failed:",
            error
        );

    }
}


// =====================================================
// AUTO REFRESH EVERY 30 SECONDS
// =====================================================

setInterval(
    function() {

        refreshDonorNotifications();

    },
    30000
);


// =====================================================
// REQUEST BROWSER NOTIFICATION PERMISSION
// =====================================================

async function requestNotificationPermission() {

    if (
        !("Notification" in window)
    ) {

        console.log(
            "Browser notifications are not supported."
        );

        return false;
    }


    if (
        Notification.permission ===
        "granted"
    ) {

        return true;
    }


    if (
        Notification.permission ===
        "denied"
    ) {

        console.log(
            "Notification permission is blocked."
        );

        return false;
    }


    try {

        const permission =
            await Notification.requestPermission();


        if (
            permission ===
            "granted"
        ) {

            console.log(
                "Notification permission granted."
            );

            return true;
        }


        console.log(
            "Notification permission not granted."
        );

        return false;

    }

    catch (error) {

        console.error(
            "Notification permission error:",
            error
        );

        return false;

    }
}


// =====================================================
// ENABLE DONOR PUSH
// =====================================================

async function enableDonorPush() {

    const donorId =
        localStorage.getItem(
            "donorId"
        );


    if (!donorId) {

        console.log(
            "Donor not logged in."
        );

        return;
    }


    const permission =
        await requestNotificationPermission();


    if (!permission) {

        return;
    }


    await subscribeToPushNotifications(
        donorId
    );
}


// =====================================================
// TEST BROWSER NOTIFICATION
// =====================================================

function testBrowserNotification() {

    if (
        Notification.permission !==
        "granted"
    ) {

        console.log(
            "Notification permission is not granted."
        );

        return;
    }


    new Notification(
        "🩸 LifeLink AI",
        {

            body:
                "Push notification test successful!",

            icon:
                "icon.png"

        }
    );
}


// =====================================================
// HOSPITAL REQUEST VALIDATION
// =====================================================

function validateHospitalRequest() {

    const hospitalId =
        document.getElementById(
            "hospital-id"
        ).value;


    const bloodGroup =
        document.getElementById(
            "blood-group"
        ).value;


    const units =
        document.getElementById(
            "units-required"
        ).value;


    const city =
        document.getElementById(
            "city"
        ).value.trim();


    if (!hospitalId) {

        alert(
            "Hospital ID is required."
        );

        return false;
    }


    if (!bloodGroup) {

        alert(
            "Please select a blood group."
        );

        return false;
    }


    if (!units || Number(units) < 1) {

        alert(
            "Units required must be at least 1."
        );

        return false;
    }


    if (!city) {

        alert(
            "City is required."
        );

        return false;
    }


    return true;
}


// =====================================================
// CHECK SERVER CONNECTION
// =====================================================

async function checkServerConnection() {

    try {

        const response =
            await fetch(
                `${API_URL}/`
            );


        if (response.ok) {

            console.log(
                "✅ Backend server connected."
            );

            return true;
        }


        console.log(
            "⚠️ Backend server responded with error."
        );

        return false;

    }

    catch (error) {

        console.error(
            "❌ Backend server connection failed:",
            error
        );

        return false;

    }
}


// =====================================================
// CHECK SERVER WHEN PAGE LOADS
// =====================================================

window.addEventListener(
    "load",
    function() {

        checkServerConnection();

    }
);
