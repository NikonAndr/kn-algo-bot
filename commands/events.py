import discord
from datetime import datetime, timedelta
from discord.ext import commands
from utils import checks
from database import events as events_db
from services import calendar_service
from services.calendar_poll_service import CalendarPollService
from utils.time_helpers import warsaw_now, parse_naive_timestamp

def next_full_hour():
    return (warsaw_now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

def format_events_list(events):

    if not events:
        return "There are no upcoming events."

    message = "Upcoming Events\n"

    for event in events:
        date = parse_naive_timestamp(event[4]).strftime("%d %b %H:%M")
        message += f"- {event[2]} ({event[6]}) — {date}\n"

    return message

class SelfCleaningView(discord.ui.View):

    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.message = None

    async def on_timeout(self):

        if self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass

class CreateEventModal(discord.ui.Modal, title="Create Event"):

    def __init__(self):
        super().__init__()

        self.title_input = discord.ui.TextInput(
            label="Title",
            max_length=200
        )

        self.description_input = discord.ui.TextInput(
            label="Description",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=False
        )

        self.start_input = discord.ui.TextInput(
            label="Start (YYYY-MM-DD HH:MM)",
            default=next_full_hour().strftime("%Y-%m-%d %H:%M"),
            max_length=20
        )

        self.duration_input = discord.ui.TextInput(
            label="Duration (minutes)",
            default="60",
            max_length=5
        )

        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.start_input)
        self.add_item(self.duration_input)

    async def on_submit(self, interaction: discord.Interaction):

        title = self.title_input.value
        description = self.description_input.value

        errors = []
        start_time = None
        end_time = None

        try:
            start_time = datetime.strptime(self.start_input.value, "%Y-%m-%d %H:%M")
        except ValueError:
            errors.append("Start must be in the format YYYY-MM-DD HH:MM.")

        try:
            duration = int(self.duration_input.value)

            if duration <= 0:
                errors.append("Duration must be a positive number of minutes.")
            elif start_time:
                end_time = start_time + timedelta(minutes=duration)
        except ValueError:
            errors.append("Duration must be a whole number of minutes.")

        if errors:
            view = SelfCleaningView(timeout=180)
            await interaction.response.send_message(
                "\n".join(errors),
                ephemeral=True,
                view=view
            )
            view.message = await interaction.original_response()
            return

        now = warsaw_now()
        is_past = start_time < now
        is_far_future = start_time >= now + timedelta(days=90)

        if is_past or is_far_future:
            reason = "in the past" if is_past else "more than 3 months from now"
            view = ConfirmSuspiciousDateView(title, description, start_time, end_time, interaction.user.id)

            await interaction.response.send_message(
                f"This event's start time is {reason} ({start_time.strftime('%d %b %Y %H:%M')}). Are you sure?",
                view=view,
                ephemeral=True
            )
            view.message = await interaction.original_response()
            return

        view = EventOptionsView(title, description, start_time, end_time, interaction.user.id)

        await interaction.response.send_message(
            "Pick an event type and reminders, then confirm:",
            view=view,
            ephemeral=True
        )
        view.message = await interaction.original_response()

class EventTypeSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(label="Club Meeting", value="club_meeting"),
            discord.SelectOption(label="Project Meeting", value="project_meeting"),
            discord.SelectOption(label="Other", value="other", default=True),
        ]

        super().__init__(placeholder="Select event type", options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.event_type = self.values[0]
        await interaction.response.defer()

class ReminderOffsetSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(label="1 day before", value="1440"),
            discord.SelectOption(label="1 hour before", value="60"),
            discord.SelectOption(label="10 minutes before", value="10"),
        ]

        super().__init__(
            placeholder="Select reminders (optional)",
            options=options,
            min_values=0,
            max_values=3
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.reminder_offsets = [int(value) for value in self.values]
        await interaction.response.defer()

class ConfirmCreateEventButton(discord.ui.Button):

    def __init__(self):
        super().__init__(
            label="Create Event",
            style=discord.ButtonStyle.green
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view

        await interaction.response.defer()

        google_event_id = calendar_service.create_event(
            view.event_title, view.event_description, view.start_time, view.end_time
        )

        event_id = events_db.create_event(
            google_event_id, view.event_title, view.event_description,
            view.start_time, view.end_time, view.event_type, "bot", view.created_by
        )

        for offset in view.reminder_offsets:
            events_db.add_reminder(event_id, offset, view.start_time - timedelta(minutes=offset))

        cleanup_view = SelfCleaningView(timeout=60)
        await interaction.edit_original_response(
            content=f"Event created: **{view.event_title}** ✅",
            view=cleanup_view
        )
        cleanup_view.message = interaction.message

class ConfirmSuspiciousDateButton(discord.ui.Button):

    def __init__(self, title, description, start_time, end_time, created_by):
        super().__init__(
            label="Yes, continue",
            style=discord.ButtonStyle.green
        )

        self.event_title = title
        self.event_description = description
        self.start_time = start_time
        self.end_time = end_time
        self.created_by = created_by

    async def callback(self, interaction: discord.Interaction):
        view = EventOptionsView(
            self.event_title, self.event_description, self.start_time, self.end_time, self.created_by
        )

        await interaction.response.edit_message(
            content="Pick an event type and reminders, then confirm:",
            view=view
        )
        view.message = interaction.message

class CancelCreateEventButton(discord.ui.Button):

    def __init__(self):
        super().__init__(
            label="Cancel",
            style=discord.ButtonStyle.gray
        )

    async def callback(self, interaction: discord.Interaction):
        view = SelfCleaningView(timeout=60)
        await interaction.response.edit_message(
            content="Event creation cancelled",
            view=view
        )
        view.message = interaction.message

class ConfirmSuspiciousDateView(SelfCleaningView):

    def __init__(self, title, description, start_time, end_time, created_by):
        super().__init__(timeout=120)

        self.add_item(ConfirmSuspiciousDateButton(title, description, start_time, end_time, created_by))
        self.add_item(CancelCreateEventButton())

class EventOptionsView(SelfCleaningView):

    def __init__(self, title, description, start_time, end_time, created_by):
        super().__init__(timeout=180)

        self.event_title = title
        self.event_description = description
        self.start_time = start_time
        self.end_time = end_time
        self.created_by = created_by
        self.event_type = "other"
        self.reminder_offsets = []

        self.add_item(EventTypeSelect())
        self.add_item(ReminderOffsetSelect())
        self.add_item(ConfirmCreateEventButton())

class DeleteEventDropdown(discord.ui.Select):

    def __init__(self, events):

        options = []

        for event in events:
            date = parse_naive_timestamp(event[4]).strftime("%d %b %H:%M")
            options.append(
                discord.SelectOption(
                    label=event[2],
                    description=f"{event[6]} — {date}",
                    value=str(event[0])
                )
            )

        super().__init__(
            placeholder="Select an event to delete",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        event_id = int(self.values[0])
        event = events_db.get_event(event_id)

        if not event or event[9] != "active":
            view = SelfCleaningView(timeout=180)
            await interaction.response.edit_message(
                content=f"That event was already deleted.\n\n{format_events_list(events_db.get_upcoming_events(limit=10))}",
                view=view
            )
            view.message = interaction.message
            self.view.stop()
            return

        view = ConfirmDeleteEventView(event_id)

        await interaction.response.edit_message(
            content=f"Delete **{event[2]}**? This cannot be undone.",
            view=view
        )
        view.message = interaction.message
        self.view.stop()

class ConfirmDeleteEventButton(discord.ui.Button):

    def __init__(self, event_id):
        super().__init__(
            label="Delete",
            style=discord.ButtonStyle.red
        )

        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction):

        await interaction.response.defer()

        event = events_db.get_event(self.event_id)

        if not event or event[9] != "active":
            cleanup_view = SelfCleaningView(timeout=180)
            await interaction.edit_original_response(
                content=f"That event was already deleted.\n\n{format_events_list(events_db.get_upcoming_events(limit=10))}",
                view=cleanup_view
            )
            cleanup_view.message = interaction.message
            self.view.stop()
            return

        calendar_service.delete_event(event[1])
        events_db.mark_event_cancelled(self.event_id)
        events_db.cancel_reminders(self.event_id)

        upcoming = events_db.get_upcoming_events(limit=10)

        cleanup_view = SelfCleaningView(timeout=180)
        await interaction.edit_original_response(
            content=f"Event deleted 🗑️\n\n{format_events_list(upcoming)}",
            view=cleanup_view
        )
        cleanup_view.message = interaction.message
        self.view.stop()

class CancelDeleteEventButton(discord.ui.Button):

    def __init__(self, event_id):
        super().__init__(
            label="Cancel",
            style=discord.ButtonStyle.gray
        )

        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction):

        view = SelfCleaningView(timeout=180)
        await interaction.response.edit_message(
            content="Deletion cancelled",
            view=view
        )
        view.message = interaction.message
        self.view.stop()

class ConfirmDeleteEventView(SelfCleaningView):

    def __init__(self, event_id):
        super().__init__(timeout=60)

        self.add_item(ConfirmDeleteEventButton(event_id))
        self.add_item(CancelDeleteEventButton(event_id))

class DeleteEventView(SelfCleaningView):

    def __init__(self, events):
        super().__init__(timeout=120)

        self.add_item(DeleteEventDropdown(events))

class DeleteEventButton(discord.ui.Button):

    def __init__(self, events):
        super().__init__(
            label="Delete Event",
            style=discord.ButtonStyle.red
        )

        self.events = events

    async def callback(self, interaction: discord.Interaction):

        view = DeleteEventView(self.events)

        await interaction.response.send_message(
            "Select an event to delete:",
            view=view,
            ephemeral=True
        )
        view.message = await interaction.original_response()
        await interaction.message.delete()

class EventsMenuView(SelfCleaningView):

    def __init__(self, events):
        super().__init__(timeout=180)
        self.events = events

        if events:
            self.add_item(DeleteEventButton(events))

class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.poller = CalendarPollService(bot)

    def cog_unload(self):
        self.poller.poll_loop.cancel()

    @commands.hybrid_command(name="create-event", description="Creates an event in the Google Calendar")
    @checks.bot_admin_only()
    async def create_event(self, ctx):
        modal = CreateEventModal()
        await ctx.interaction.response.send_modal(modal)

    @commands.hybrid_command(name="events", description="Lists upcoming events from the Google Calendar")
    @checks.bot_admin_only()
    async def list_events(self, ctx):
        upcoming = events_db.get_upcoming_events(limit=10)

        view = EventsMenuView(upcoming)

        sent_message = await ctx.send(format_events_list(upcoming), view=view, ephemeral=True)
        view.message = sent_message

async def setup(bot):
    await bot.add_cog(Events(bot))
