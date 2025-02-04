# Calendar

Fetch ICS calendar and return events for the current week.

## Install

```
$ uv sync
```

## Environment variables

- `USER_TOKEN`: token of the main user
- `ICS_URL`: url of the ICS calendar to fetch

## Local Run

```
env USER_TOKEN=... ICS_URL=... uv run
```

## Deployment

Deployed as a function on DigitalOcean cloud platform

```
doctl serverless deploy (--context main) .

# Getting url to call to invoke function
doctl serverless function get calendar-api/weekly --url (--context main)
```
