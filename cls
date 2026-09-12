warning: in the working copy of 'frontend/donor-pages.js', LF will be replaced by CRLF the next time Git touches it
[1mdiff --git a/frontend/donor-pages.js b/frontend/donor-pages.js[m
[1mindex 5bc9f00..172107a 100644[m
[1m--- a/frontend/donor-pages.js[m
[1m+++ b/frontend/donor-pages.js[m
[36m@@ -1,4 +1,4 @@[m
[31m-const DONOR_API_URL = "http://127.0.0.1:8000";[m
[32m+[m[32mconst DONOR_API_URL = "https://raktanova-backend.onrender.com";[m
 [m
 const DONOR_VAPID_PUBLIC_KEY =[m
     "BATkLbDGETZD-IlWwmdQhrDkSRTmShmgGoMV2IeroAKc2DHEinkXRue4XrUiK0Oc7bUqho3NllLlqy2Plz0rCwE";[m
[1mdiff --git a/frontend/script.js b/frontend/script.js[m
[1mindex 361978f..808191e 100644[m
[1m--- a/frontend/script.js[m
[1m+++ b/frontend/script.js[m
[36m@@ -1,7 +1,7 @@[m
 console.log("SCRIPT LOADED");[m
 [m
 [m
[31m-const API_URL = "http://127.0.0.1:8000";[m
[32m+[m[32mconst API_URL = "https://raktanova-backend.onrender.com";[m
 [m
 [m
 // Holds GPS captured for the donor registration form[m
