"""Draft PRs are not announced until they're marked ready for review."""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from database import github_events
from services import github_poll_service
from services.github_poll_service import GithubPollService

REPO = "KN-Algo/bot"


class FakeChannel:
    def __init__(self):
        self.sent = []

    async def send(self, message):
        self.sent.append(message)


class FakeBot:
    def __init__(self, channel):
        self.channel = channel

    async def wait_until_ready(self):
        pass

    def get_channel(self, channel_id):
        return self.channel


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def make_pr(number, draft, created_ago, updated_ago=timedelta(0)):
    now = datetime.now(timezone.utc)
    return {
        "number": number,
        "draft": draft,
        "title": f"PR {number}",
        "html_url": f"https://github.com/{REPO}/pull/{number}",
        "user": {"login": "alice"},
        "requested_reviewers": [],
        "created_at": iso(now - created_ago),
        "updated_at": iso(now - updated_ago),
        "merged_at": None,
    }


@pytest.fixture
def poller(temp_db, monkeypatch):
    """A GithubPollService whose PR list is controlled by the test."""
    monkeypatch.setattr(github_poll_service, "GH_UPDATES_CHANNEL_ID", "1")
    # Repo already seen before, so new PRs get announced (not silently seeded).
    github_events.mark_notified(REPO, 999, "opened")

    channel = FakeChannel()
    state = {"pulls": []}

    async def no_refresh(self):
        pass

    async def fake_pulls(self, full_name):
        return state["pulls"]

    monkeypatch.setattr(GithubPollService, "refresh_tracked_repos", no_refresh)
    monkeypatch.setattr(GithubPollService, "get_pull_requests", fake_pulls)

    def poll(pulls):
        state["pulls"] = pulls

        async def scenario():
            service = GithubPollService(FakeBot(channel))
            service.poll_loop.cancel()
            service.tracked_repos = [REPO]
            await service.poll_once()

        asyncio.run(scenario())
        return channel.sent

    return poll


def test_draft_pr_is_not_announced(poller):
    sent = poller([make_pr(1, draft=True, created_ago=timedelta(minutes=5))])

    assert sent == []


def test_draft_is_announced_once_marked_ready(poller):
    sent_while_draft = list(poller([make_pr(1, draft=True, created_ago=timedelta(minutes=5))]))

    sent = poller([make_pr(1, draft=False, created_ago=timedelta(minutes=5))])

    assert sent_while_draft == []
    assert len(sent) == 1 and "opened a PR" in sent[0]


def test_long_lived_draft_is_announced_when_marked_ready(poller):
    # Draft opened 3 days ago, marked ready just now: created_at is stale,
    # but the PR is new to reviewers, so it must still be announced.
    sent = poller([make_pr(1, draft=False, created_ago=timedelta(days=3), updated_ago=timedelta(0))])

    assert len(sent) == 1


def test_ready_pr_is_announced_only_once(poller):
    pr = make_pr(1, draft=False, created_ago=timedelta(minutes=5))
    poller([pr])

    sent = poller([pr])

    assert len(sent) == 1
