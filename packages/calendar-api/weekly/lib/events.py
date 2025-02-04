from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo
from enum import Enum, StrEnum
from typing import List, Self, Tuple
from zoneinfo import ZoneInfo


UTC = ZoneInfo("UTC")


class DateUtils:
    @classmethod
    def parse_date(
        cls, raw_string: str, timezone: tzinfo, is_date: bool = False
    ) -> datetime:
        date: datetime
        if is_date:
            date = datetime.strptime(raw_string, "%Y%m%d")
        else:
            date = datetime.fromisoformat(raw_string)
        # Events that include a timezone through TZID have already timezone aware hours.
        if raw_string[-1] != "Z":
            return date.replace(tzinfo=timezone)
        # UTC events are transformed to a timezone aware datetime
        return date.astimezone(timezone)

    @classmethod
    def week(cls, date: datetime) -> Tuple[datetime, datetime]:
        day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        start = day - timedelta(days=day.weekday())  # Monday
        end = start + timedelta(days=7)  # Sunday
        return start, end


class ParserNotCalledError(Exception):
    def __str__(self) -> str:
        return "Parse an ICS file before calling this method"


class InvalidTokenError(Exception):
    def __str__(self) -> str:
        return "Invalid token"


class InvalidEventError(Exception):
    def __str__(self) -> str:
        return "Invalid event."


class Token(StrEnum):
    @classmethod
    def include(cls, token: str) -> bool:
        try:
            cls(token)
            return True
        except Exception:
            return False


class CalendarToken(Token):
    Timezone = "TZID"
    Begin = "BEGIN"
    End = "END"
    Event = "VEVENT"


class EventToken(Token):
    Summary = "SUMMARY"
    DateStart = "DTSTART"
    DateEnd = "DTEND"
    RepeatingEventRule = "RRULE"

    @classmethod
    def include(cls, token: str) -> bool:
        return (
            super().include(token)
            or token.startswith(EventToken.DateStart)
            or token.startswith(EventToken.DateEnd)
        )


class RuleToken(Token):
    Frequency = "FREQ"
    Until = "UNTIL"
    Interval = "INTERVAL"
    ByDay = "BYDAY"


class Frequency(Enum):
    DAILY = timedelta(days=1)
    WEEKLY = timedelta(weeks=1)
    YEARLY = timedelta(days=365)


class Day(Enum):
    Monday = "MO"
    Tuesday = "TU"
    Wednesday = "WE"
    Thursday = "TH"
    Friday = "FR"
    Saturday = "SA"
    Sunday = "SU"


@dataclass
class Rule:
    frequency: Frequency
    until: datetime | None = None
    interval: int | None = None
    by_day: Day | None = None

    @property
    def finished(self) -> bool:
        return self.until is not None and datetime.now(UTC) > self.until

    def __str__(self) -> str:
        by_day = self.by_day and f" on the {self.by_day.name.lower()}" or ""
        interval = self.interval and f"every {self.interval} " or ""
        finished = self.finished and " (finished)" or ""
        return f"Repeating {interval}{self.frequency.name.lower()}{by_day}{finished}."

    @classmethod
    def parse_ics_rule(cls, rule: str, timezone: tzinfo) -> Self | None:
        frequency: Frequency
        until: datetime | None = None
        interval: int | None = None
        by_day: Day | None = None

        instructions = rule.split(";")

        for instruction in instructions:
            token, content = instruction.strip().split("=")
            if token == RuleToken.Frequency:
                try:
                    frequency = Frequency[content]
                except Exception:
                    return None
            if token == RuleToken.Until:
                until = DateUtils.parse_date(content, timezone)
            if token == RuleToken.Interval:
                interval = int(content)
            if token == RuleToken.ByDay:
                by_day = Day(content)

        return cls(frequency=frequency, until=until, interval=interval, by_day=by_day)


@dataclass
class Event:
    all_day: bool = False
    rule: Rule | None = None
    begin: datetime | None = None
    end: datetime | None = None
    name: str = ""

    @property
    def date(self) -> datetime:
        if self.begin is None:
            raise InvalidEventError()
        return self.begin

    @property
    def repeating(self) -> bool:
        return self.rule is not None

    @property
    def day(self) -> int:
        return self.date.day

    @property
    def day_label(self) -> str:
        return self.date.strftime("%a")

    @property
    def month(self) -> int:
        return self.date.month

    @property
    def month_label(self) -> str:
        return self.date.strftime("%b")

    @property
    def year(self) -> int:
        return self.date.year

    @property
    def time(self) -> str:
        return self.date.strftime("%H:%M")

    def __repr__(self):
        is_repeating = self.repeating and f". {self.rule}" or ""
        is_all_day = self.all_day and "All-day " or ""
        return f"<class {is_all_day}{type(self).__name__}: {self}{is_repeating}>"

    def __str__(self) -> str:
        return "{} {} {} {}".format(self.month_label, self.day, self.time, self.name)

    @property
    def __dict__(self):
        return {
            "all_day": self.all_day,
            "repeating": self.repeating,
            "name": self.name,
            "date": self.date.isoformat(),
            "day": self.day,
            "dayLabel": self.day_label,
            "year": self.year,
            "month": self.month,
            "monthLabel": self.month_label,
            "time": self.time,
        }

    @classmethod
    def _parse_date_token(cls, token) -> Tuple[bool, tzinfo | None]:
        parts = token.split(";")
        all_day = False
        timezone: tzinfo | None = None

        for part in parts:
            try:
                token, content = part.split("=")

                if token == "TZID":
                    timezone = ZoneInfo(content)
                if token == "VALUE":
                    all_day = True
            except Exception:
                continue

        return all_day, timezone

    @classmethod
    def parse_ics(cls, text: str):
        events = []
        timezone: tzinfo = UTC
        event: Event | None = None

        for line in text.split("\n"):
            # Parse tag content
            try:
                (token, content) = line.strip().split(":", maxsplit=1)
                # Token validation
                if not (
                    CalendarToken.include(token)
                    or RuleToken.include(token)
                    or EventToken.include(token)
                ):
                    raise InvalidTokenError()
            except Exception:
                continue

            if token == CalendarToken.Timezone:
                timezone = ZoneInfo(content)

            # Manage event parsing lifecycle
            is_event = content == CalendarToken.Event
            if token == CalendarToken.Begin and is_event:
                event = Event()
                continue
            elif token == CalendarToken.End and is_event and event is not None:
                events.append(event)
                event = None
            if event is None:
                continue

            if token == EventToken.Summary:
                event.name = content.replace("\\", "")
            elif token.startswith(EventToken.DateStart):
                all_day, event_timezone = cls._parse_date_token(token)
                event.all_day = all_day
                event.begin = DateUtils.parse_date(
                    content, event_timezone or timezone, is_date=all_day
                )
            elif token.startswith(EventToken.DateEnd):
                all_day, event_timezone = cls._parse_date_token(token)
                event.all_day = all_day
                event.end = DateUtils.parse_date(
                    content, event_timezone or timezone, is_date=all_day
                )
            elif token == "RRULE":
                event.rule = Rule.parse_ics_rule(content, timezone)

        cls.events = events
        cls.timezone = timezone

        return events

    @classmethod
    def included(cls, begin: datetime, end: datetime) -> List[Event]:
        events = [e for e in cls.events if e.begin > begin and e.end < end]
        repeating = [
            e
            for e in cls.events
            if e.repeating and (e.rule.until is None or e.rule.until > end)
        ]

        for e in repeating:
            if e.rule.frequency == Frequency.YEARLY:
                date = e.begin.replace(year=begin.year)

                if date > e.begin and date < e.end:
                    events.append(e)
            elif e.rule.frequency == Frequency.WEEKLY:
                # get the day of the week
                day = e.begin.weekday()

                # compute on which day the event would occur in the interval
                computed_date = begin + timedelta(days=day)
                # replace hour and minute components with the original value
                computed_date = computed_date.replace(
                    hour=e.begin.hour, minute=e.begin.minute
                )
                # get the duration of the event
                duration = e.begin - e.end

                # Update the event begin and end properties
                e.begin = computed_date
                e.end = computed_date + duration
                events.append(e)
        # TODO: Implement DAILY, ByDay and Interval
        events.sort(key=lambda e: e.begin)
        return events

    @classmethod
    def current_week(cls) -> List[Event]:
        if not cls.events:
            raise ParserNotCalledError

        start, end = DateUtils.week(datetime.now(cls.timezone))
        return list(cls.included(start, end))
