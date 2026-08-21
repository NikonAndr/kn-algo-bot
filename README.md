<div align="center">

# KN ALGO Discord Bot

**A Discord Bot for KN ALGO Science club at the Wroclaw University of Science and Technology**

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-hybrid%20commands-5865F2?logo=discord&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)

</div>

**Status:** in active use on the KN ALGO Discord server.

## About

Started as a small utility bot and grew into the club's integration point between Discord, Google Calendar, GitHub, and email. The interesting part isn't any single command - it's keeping three external systems (Calendar, a GitHub org, an SMTP inbox) mirrored into one SQLite database without double-posting or losing state on restart.

## Features

* **Calendar-synced events** - `/events` lists upcoming events pulled from Google Calendar; a poll loop keeps creates/updates/cancellations in sync and schedules automatic Discord reminders before each one starts
* **Weekly notes digest** - `/note` lets members draft and self-approve short notes through a modal; approved notes for the week are emailed out to a subscriber list on a rolling interval. We use it to email project progress to our supervisers. 
* **Subscriber management** - bot-admin-only `/subscribe`, `/unsubscribe`, `/subscribers` commands manage the weekly-digest email list
* **GitHub PR notifications** - polls every repo in a configured GitHub org and posts "opened" / "merged" events to a dedicated channel
* **Daily horoscope** - dropdown zodiac picker, fetched per sign
* **Meme command** - posts a random image from a local `memes/` folder
* **Role-based permissions** - member / team lead / bot admin tiers, enforced per-command through a small decorator library
* **Generic task scheduler** - one loop drives event reminders, the weekly digest send, and ad-hoc scheduled messages, all persisted in SQLite so nothing is lost on restart

## Database

Bot uses a simple sqlite database. On the first run bot is going to create an empty `data/database.db` file. The database itself contains 6 tables: 
* `subscribers` - stores emails of subsribers.
* `scheduled_tasks` - stores the scheduled tasks. Used by Weekly Notes service. 
* `notified_events` - stores the info about opened/merged Pull Requests.
* `events` - stores the Google Calendar events.
* `event_reminders` - stores the default/selected reminders about Google Calendar events.

Weekly Backups are created at `data/backups`.

### Setup & run

Before running the bot move your google-service account json into `credentials/`!

```bash
git clone https://github.com/NikonAndr/kn-algo-bot
cd kn-algo-bot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in the values below
python bot.py
```

For explicit help **Written in Polish** visit [Admin Help](ADMIN_HELP.md).

### Configuration

All configuration is read from `.env` by `config.py`:

| Variable | Used for |
|---|---|
| `DISCORD_TOKEN` | token generated on the discord dev portal |
| `BOT_ADMIN_ROLE_ID`, `TEAM_LEAD_ROLE_ID`, `MEMBER_ROLE_ID` | permission tiers (see below) |
| `GOOGLE_SERVICE_ACCOUNT_FILE`, `GOOGLE_CALENDAR_ID` | Calendar sync (service-account JSON, default path `credentials/google-service-account.json`) |
| `CALENDAR_UPDATES_CHANNEL_ID` | where to post a calendar updates |
| `GITHUB_TOKEN`, `GITHUB_ORG`, `GH_UPDATES_CHANNEL_ID` | PR polling |
| `EMAIL_ADDRESS`, `EMAIL_PASSWORD` | Gmail SMTP for the weekly digest |

### Permissions

Three role tiers, checked in `utils/checks.py` / `services/permission_service.py` and mapped to Discord role IDs in `.env`: **member** (baseline - create_event, events, horoscope, meme, ping), **team-lead** (weekly notes management - note) and **bot admin**, which currently gates the subscriber-list commands. Each command declares its required tier with a decorator, so adding a new gated command is a one-line change.

## Tech Stack

* Python 3.10+
* [discord.py](https://discordpy.readthedocs.io/) - hybrid slash + prefix commands
* SQLite via raw `sqlite3` (no ORM)
* Google Calendar API (`google-api-python-client`, service-account auth)
* GitHub REST API via `aiohttp` (polling, no webhooks)
* Gmail SMTP (`smtplib`) for the weekly notes digest
* `pytest` for the test suite (`tests/`)
