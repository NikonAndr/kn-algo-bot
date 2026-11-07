from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import GOOGLE_SERVICE_ACCOUNT_FILE, GOOGLE_CALENDAR_ID
from utils.time_helpers import WARSAW_TZ

SCOPES = ["https://www.googleapis.com/auth/calendar"]

_client = None

def get_client():
    global _client

    if _client is None:
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        _client = build("calendar", "v3", credentials=credentials)

    return _client

def list_events(time_min, time_max):
    client = get_client()

    items = []
    page_token = None

    # Google returns at most 250 events per page; follow nextPageToken so
    # nothing past the first page is silently dropped.
    while True:
        result = client.events().list(
            calendarId=GOOGLE_CALENDAR_ID,
            timeMin=time_min.replace(tzinfo=WARSAW_TZ).isoformat(),
            timeMax=time_max.replace(tzinfo=WARSAW_TZ).isoformat(),
            showDeleted=True,
            singleEvents=True,
            orderBy="startTime",
            pageToken=page_token,
        ).execute()

        items.extend(result.get("items", []))
        page_token = result.get("nextPageToken")

        if not page_token:
            return items

def create_event(title, description, start_time, end_time, location=""):
    client = get_client()

    body = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_time.isoformat(), "timeZone": "Europe/Warsaw"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "Europe/Warsaw"},
    }

    if location:
        body["location"] = location

    created = client.events().insert(calendarId=GOOGLE_CALENDAR_ID, body=body).execute()

    return created["id"]

def delete_event(google_event_id):
    client = get_client()

    try:
        client.events().delete(calendarId=GOOGLE_CALENDAR_ID, eventId=google_event_id).execute()
    except HttpError as error:
        if error.resp.status not in (404, 410):
            raise
