from os import environ
import sys

# Add modules to the path
sys.path.append("./packages/calendar-api/weekly")

from requests import get as fetch

from lib.events import Event

url = environ.get("ICS_URL")

if url is None:
    raise Exception("Invalid or missing ICS_URL environment variable")

assert url


def weekly_calendar(text):
    Event.parse_ics(text)
    return {"events": [e.__dict__ for e in Event.current_week()]}


if __name__ == "__main__":
    text: str = ""

    if url:
        text = fetch(url).text
    else:
        try:
            with open("calendar.ics") as f:
                text = f.read()
        except Exception:
            raise Exception("Invalid url and no local ICS file found.")

    print(weekly_calendar(text))
