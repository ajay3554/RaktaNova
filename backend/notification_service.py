import json
from pathlib import Path
from pywebpush import webpush, WebPushException
PRIVATE_KEY_FILE = (
    Path(__file__).parent /
    "private_key.pem"
)

VAPID_PRIVATE_KEY = str(PRIVATE_KEY_FILE)

VAPID_CLAIMS = {
    "sub": "mailto:ajay67068@gmail.com"
}
def send_push_notification(
    subscription,
    title,
    message
):

    try:

        payload = json.dumps({
            "title": title,
            "body": message,
            "url": "/frontend/index.html"
        })

        webpush(
            subscription_info=subscription,
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )

        print("================================")
        print("PUSH NOTIFICATION SENT")
        print("Message:", message)
        print("================================")

        return True

    except WebPushException as error:

        print("================================")
        print("PUSH NOTIFICATION FAILED")
        print(error)
        print("================================")

        return False


