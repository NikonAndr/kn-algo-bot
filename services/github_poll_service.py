import aiohttp
from datetime import datetime, timedelta, timezone
from discord.ext import tasks

from config import GITHUB_TOKEN, GH_UPDATES_CHANNEL_ID, GITHUB_TRACKED_REPOS
from database.github_events import is_notified, mark_notified, has_any_events

GITHUB_API_URL = "https://api.github.com"
STALE_EVENT_THRESHOLD = timedelta(hours=24)


def parse_github_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class GithubPollService:

    def __init__(self, bot):
        self.bot = bot
        self.session = None
        self.poll_loop.start()

    def cog_unload(self):
        self.poll_loop.cancel()

    async def get_pull_requests(self, full_name):
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }

        url = f"{GITHUB_API_URL}/repos/{full_name}/pulls?state=all&sort=updated&direction=desc&per_page=100"

        async with self.session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return []
            return await resp.json()

    async def get_merged_by(self, full_name, pr_number, fallback_author):
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }

        url = f"{GITHUB_API_URL}/repos/{full_name}/pulls/{pr_number}"

        async with self.session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return fallback_author
            detail = await resp.json()
            merged_by = detail.get("merged_by")
            return merged_by["login"] if merged_by else fallback_author

    async def handle_event(self, channel, repo, pr, event_type, event_time_field, seeded, message_builder):
        pr_number = pr["number"]

        if is_notified(repo, pr_number, event_type):
            return

        event_time = parse_github_time(pr[event_time_field])
        is_fresh = (datetime.now(timezone.utc) - event_time) <= STALE_EVENT_THRESHOLD

        if seeded and is_fresh and channel:
            message = await message_builder()
            await channel.send(message)

        mark_notified(repo, pr_number, event_type)

    @tasks.loop(seconds=30)
    async def poll_loop(self):

        channel = self.bot.get_channel(int(GH_UPDATES_CHANNEL_ID)) if GH_UPDATES_CHANNEL_ID else None

        for full_name in GITHUB_TRACKED_REPOS:
            seeded = has_any_events(full_name)

            pulls = await self.get_pull_requests(full_name)

            for pr in pulls:
                author = pr["user"]["login"]
                title = pr["title"]
                url = pr["html_url"]

                reviewers = [r["login"] for r in pr.get("requested_reviewers", [])]
                reviewers_line = f"Reviewers: {', '.join(reviewers)}" if reviewers else "Reviewers: none requested"

                async def build_opened_message(author=author, title=title, reviewers_line=reviewers_line, url=url, full_name=full_name):
                    return f"📢 **{author}** opened a PR in **{full_name}**: {title}\n{reviewers_line}\n{url}"

                await self.handle_event(
                    channel, full_name, pr, "opened", "created_at", seeded, build_opened_message
                )

                if pr.get("merged_at"):
                    async def build_merged_message(pr_number=pr["number"], author=author, title=title, url=url, full_name=full_name):
                        merged_by = await self.get_merged_by(full_name, pr_number, author)
                        return f"✅ PR merged in **{full_name}**: {title} (by {merged_by})\n{url}"

                    await self.handle_event(
                        channel, full_name, pr, "merged", "merged_at", seeded, build_merged_message
                    )

    @poll_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
        self.session = aiohttp.ClientSession()
