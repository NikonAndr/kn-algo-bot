"""Background loops must survive errors instead of dying silently.

Each test starts the real discord.ext.tasks loop, lets it run one iteration
against fakes, and checks the loop is still alive afterwards.
"""
import asyncio
from datetime import timedelta

import httplib2
import pytest

from database import events as events_db
from database import scheduled_tasks
from services import calendar_service, email_service, notes_service
from services import scheduler_service
from services.calendar_poll_service import CalendarPollService
from services.github_poll_service import GithubPollService
from services.scheduler_service import SchedulerService
from utils.time_helpers import warsaw_now


class FakeChannel:
    def __init__(self, fail_on=()):
        self.sent = []
        self.fail_on = set(fail_on)

    async def send(self, message):
        if any(marker in message for marker in self.fail_on):
            raise RuntimeError("discord send failed")
        self.sent.append(message)


class FakeBot:
    def __init__(self, channels=None):
        self.channels = channels or {}

    async def wait_until_ready(self):
        pass

    def get_channel(self, channel_id):
        return self.channels.get(channel_id)


def run_one_iteration(make_service, loop_name="poll_loop"):
    """Start a service, let its loop run once, report (is_running, failed)."""
    async def scenario():
        service = make_service()
        await asyncio.sleep(0.2)
        loop = getattr(service, loop_name)
        state = (loop.is_running(), loop.failed())
        loop.cancel()
        await asyncio.sleep(0)
        return service, state

    return asyncio.run(scenario())


def calendar_item(google_id, start="2030-01-01T10:00:00+01:00", end="2030-01-01T11:00:00+01:00"):
    return {
        "id": google_id,
        "status": "confirmed",
        "summary": f"Event {google_id}",
        "start": {"dateTime": start},
        "end": {"dateTime": end},
    }


# --- Calendar poller ---------------------------------------------------------

def test_calendar_poll_loop_survives_dns_failure(temp_db, monkeypatch):
    def unreachable(*args, **kwargs):
        raise httplib2.ServerNotFoundError("Unable to find the server at www.googleapis.com")

    monkeypatch.setattr(calendar_service, "list_events", unreachable)

    _, (running, failed) = run_one_iteration(lambda: CalendarPollService(FakeBot()))

    assert running and not failed


def test_calendar_bad_event_does_not_block_the_rest(temp_db, monkeypatch):
    broken = {"id": "broken", "status": "confirmed"}  # no start/end -> KeyError
    monkeypatch.setattr(
        calendar_service, "list_events", lambda *a, **k: [broken, calendar_item("good")]
    )

    _, (running, failed) = run_one_iteration(lambda: CalendarPollService(FakeBot()))

    assert running and not failed
    assert events_db.get_event_by_google_id("good") is not None


class FakeListRequest:
    def __init__(self, response):
        self.response = response

    def execute(self):
        return self.response


class FakeEventsResource:
    def __init__(self, pages):
        self.pages = pages

    def list(self, **kwargs):
        return FakeListRequest(self.pages[kwargs.get("pageToken")])


class FakeCalendarClient:
    def __init__(self, pages):
        self.resource = FakeEventsResource(pages)

    def events(self):
        return self.resource


def test_list_events_follows_next_page_token(monkeypatch):
    pages = {
        None: {"items": [calendar_item("a")], "nextPageToken": "page-2"},
        "page-2": {"items": [calendar_item("b")], "nextPageToken": "page-3"},
        "page-3": {"items": [calendar_item("c")]},
    }
    monkeypatch.setattr(calendar_service, "get_client", lambda: FakeCalendarClient(pages))

    now = warsaw_now()
    items = calendar_service.list_events(now, now + timedelta(days=90))

    assert [item["id"] for item in items] == ["a", "b", "c"]


# --- Scheduler -----------------------------------------------------------------

def add_due_task(task_type, payload):
    scheduled_tasks.add_task(task_type, payload, warsaw_now() - timedelta(minutes=1))


def test_scheduler_failing_task_does_not_block_others(temp_db, monkeypatch):
    monkeypatch.setattr(scheduler_service, "CALENDAR_UPDATES_CHANNEL_ID", None)
    broken_channel = FakeChannel(fail_on=["first"])
    ok_channel = FakeChannel()
    bot = FakeBot({1: broken_channel, 2: ok_channel})

    add_due_task("send_message", {"channel_id": 1, "message": "first"})
    add_due_task("send_message", {"channel_id": 2, "message": "second"})

    _, (running, failed) = run_one_iteration(lambda: SchedulerService(bot), "scheduler_loop")

    assert running and not failed
    assert ok_channel.sent == ["second"]
    # The failed task is not retried every 30s forever.
    assert not scheduled_tasks.has_pending_task("send_message")


def test_scheduler_weekly_digest_failure_still_schedules_next_week(temp_db, monkeypatch):
    monkeypatch.setattr(scheduler_service, "CALENDAR_UPDATES_CHANNEL_ID", None)
    marked_sent = []

    def smtp_down(recipients, notes):
        raise OSError("SMTP unreachable")

    monkeypatch.setattr(notes_service, "get_notes_to_send", lambda: [("note",)])
    monkeypatch.setattr(notes_service, "mark_notes_sent", marked_sent.append)
    monkeypatch.setattr(email_service, "send_weekly_notes", smtp_down)

    add_due_task("send_weekly_notes", {})

    _, (running, failed) = run_one_iteration(lambda: SchedulerService(FakeBot()), "scheduler_loop")

    assert running and not failed
    # smtplib errors are OSErrors, which discord.py retries on its own; the
    # failed digest must not stay due, or earlier recipients get it again.
    assert scheduled_tasks.get_due_tasks() == []
    assert scheduled_tasks.has_pending_task("send_weekly_notes")
    # Unsent notes stay approved, so they go out with next week's digest.
    assert marked_sent == []


def test_scheduler_failing_reminder_does_not_block_others(temp_db, monkeypatch):
    monkeypatch.setattr(scheduler_service, "CALENDAR_UPDATES_CHANNEL_ID", "10")
    monkeypatch.setattr(scheduler_service, "MEMBER_ROLE_ID", None)
    channel = FakeChannel(fail_on=["Broken"])

    start = warsaw_now() + timedelta(minutes=60)
    for title in ("Broken", "Fine"):
        event_id = events_db.create_event(None, title, "", start, start, "other", "bot", None)
        events_db.add_reminder(event_id, 60, warsaw_now() - timedelta(seconds=10))

    _, (running, failed) = run_one_iteration(
        lambda: SchedulerService(FakeBot({10: channel})), "scheduler_loop"
    )

    assert running and not failed
    assert len(channel.sent) == 1 and "Fine" in channel.sent[0]


# --- GitHub poller -------------------------------------------------------------

def test_github_poll_loop_survives_unexpected_error(temp_db, monkeypatch):
    async def explode(self):
        raise KeyError("full_name")

    monkeypatch.setattr(GithubPollService, "refresh_tracked_repos", explode)

    async def scenario():
        service = GithubPollService(FakeBot())
        await asyncio.sleep(0.2)
        state = (service.poll_loop.is_running(), service.poll_loop.failed())
        service.poll_loop.cancel()
        await asyncio.sleep(0)
        if service.session:
            await service.session.close()
        return state

    running, failed = asyncio.run(scenario())

    assert running and not failed
