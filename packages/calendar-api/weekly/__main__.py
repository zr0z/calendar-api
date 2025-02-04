from os import environ

from lib.events import Event
from lib.calendar import Week

from requests import get as fetch


user_token = environ.get("USER_TOKEN", "")
url = environ.get("ICS_URL", "")


def main(event):
    token: str | None = None
    try:
        token = event["http"]["headers"].get("authorization", None)
    except Exception:
        pass

    if token != f"Bearer {user_token}":
        return {
            "body": {
                "status": 401,
                "message": "Access denied.",
            },
            "status": 401,
        }

    try:
        text = fetch(url).text
        Event.parse_ics(text)

        return {
            "body": {
                "calendar": Week().__dict__,
                "events": [e.__dict__ for e in Event.current_week()],
                "timezone": f"{Event.timezone}",
            }
        }
    except Exception as e:
        return {
            "body": {
                "status": 500,
                "message": f"{e}",
            },
            "status": 500,
        }
