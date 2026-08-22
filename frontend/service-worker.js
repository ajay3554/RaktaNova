self.addEventListener("install", (event) => {
    console.log("Service Worker installed.");
    self.skipWaiting();
});


self.addEventListener("activate", (event) => {
    console.log("Service Worker activated.");
    event.waitUntil(
        self.clients.claim()
    );
});


self.addEventListener("push", (event) => {

    let data = {};

    if (event.data) {
        data = event.data.json();
    }

    const title =
        data.title || "LifeLink AI";

    const options = {

        body:
            data.body ||
            "You have a new blood request.",

        icon:
            "/frontend/icon.png",

        badge:
            "/frontend/icon.png",

        data:
            data.url || "/frontend/index.html"

    };

    event.waitUntil(

        self.registration.showNotification(
            title,
            options
        )

    );

});


self.addEventListener("notificationclick", (event) => {

    event.notification.close();

    event.waitUntil(

        clients.openWindow(
            event.notification.data ||
            "/frontend/index.html"
        )

    );

});