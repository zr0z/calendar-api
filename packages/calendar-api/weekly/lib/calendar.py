from zoneinfo import ZoneInfo
from datetime import datetime, timedelta


class Day:
    def __init__(self, date: datetime):
        self.date = date

    @property
    def name(self):
        return self.date.strftime("%a")[0]

    @property
    def day(self):
        return self.date.day

    @property
    def month(self):
        return self.date.strftime("%b")

    @property
    def year(self):
        return self.date.year

    def __str__(self):
        return f"{self.month} {self.day} ({self.name})"

    def __repr__(self):
        return f"<class {type(self).__name__}: {self}>"

    @property
    def __dict__(self):
        return {
            "day": self.day,
            "month": self.month,
            "year": self.year,
            "name": self.name,
        }


class Week:
    def __init__(self, date=datetime.now(tz=ZoneInfo("Asia/Tokyo"))):
        self.date = date

    @property
    def week_number(self):
        return self.date.strftime("%W")

    @property
    def year(self):
        return self.date.year

    @property
    def days_of_week(self):
        """
        Return the full week (Monday first) of the week for the current date.
        """
        monday = self.date - timedelta(days=self.date.weekday())

        return [Day(monday + timedelta(days=i)) for i in range(7)]

    @property
    def __dict__(self) -> dict:
        return {
            "year": self.year,
            "week_number": self.week_number,
            "weekdays": [d.__dict__ for d in self.days_of_week],
        }


if __name__ == "__main__":
    print(Week().__dict__)
