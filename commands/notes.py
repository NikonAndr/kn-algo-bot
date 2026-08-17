import discord
from discord.ext import commands
from services import notes_service

def word_count(text):
    return len(text.split())

def format_notes_list(notes):

    if not notes:
        return "You don't have any notes yet."

    message = "Your Notes\n"

    for note in notes:
        message += f"- {note[1]} ({note[5]})\n"

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

class CreateNoteModal(discord.ui.Modal, title="Create Weekly Note"):

    title_input = discord.ui.TextInput(
        label="Title",
        max_length=500
    )

    content_input = discord.ui.TextInput(
        label="Content",
        style=discord.TextStyle.paragraph,
        max_length=4000
    )

    async def on_submit(self, interaction: discord.Interaction):
        print("DISPLAY:", interaction.user.display_name)
        print("USERNAME:", interaction.user.name)
        print("NICK:", interaction.user.nick)

        title = self.title_input.value
        content = self.content_input.value

        errors = []

        if word_count(title) > 50:
            errors.append(f"Title is {word_count(title)} words (max 50).")

        if word_count(content) > 400:
            errors.append(f"Content is {word_count(content)} words (max 400).")

        if errors:
            await interaction.response.send_message(
                "\n".join(errors),
                ephemeral=True
            )
            return

        author_id = interaction.user.id
        author_name = interaction.user.display_name

        note_id = notes_service.create_note(title, content, author_id, author_name)

        view = ApproveDraftView(note_id)

        await interaction.response.send_message(
            "Note Created! Would you like to approve it right away?",
            view=view,
            ephemeral=True
        )
        view.message = await interaction.original_response()

class EditNoteModal(discord.ui.Modal, title="Edit Note"):

    def __init__(self, note):

        super().__init__()

        self.note_id = note[0]

        self.title_input = discord.ui.TextInput(
            label="Title",
            default=note[1],
            max_length=500
        )

        self.content_input = discord.ui.TextInput(
            label="Content",
            default=note[2],
            style=discord.TextStyle.paragraph,
            max_length=4000
        )

        self.add_item(self.title_input)
        self.add_item(self.content_input)

    async def on_submit(self, interaction: discord.Interaction):

        title = self.title_input.value
        content = self.content_input.value

        errors = []

        if word_count(title) > 50:
            errors.append(f"Title is {word_count(title)} words (max 50).")

        if word_count(content) > 400:
            errors.append(f"Content is {word_count(content)} words (max 400).")

        if errors:
            await interaction.response.send_message(
                "\n".join(errors),
                ephemeral=True
            )
            return

        notes_service.edit_note(
            self.note_id,
            title,
            content
        )

        notes = notes_service.get_user_notes(interaction.user.id)

        await interaction.response.send_message(
            f"Note updated!\n\n{format_notes_list(notes)}",
            ephemeral=True
        )

class EditNoteDropdown(discord.ui.Select):

    def __init__(self, notes):

        options = []

        for note in notes:
            options.append(
                discord.SelectOption(
                    label=note[1],
                    description=f"Status: {note[5]}",
                    value=str(note[0])
                )
            )

        super().__init__(
            placeholder="Select note to edit",
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):

        note_id = int(self.values[0])
        note = notes_service.get_note(note_id)

        modal = EditNoteModal(note)

        await interaction.response.send_modal(modal)
        await interaction.message.delete()

class StatusNoteDropdown(discord.ui.Select):

    def __init__(self, notes):

        options = []

        for note in notes:
            options.append(
                discord.SelectOption(
                    label=note[1],
                    description=f"Status: {note[5]}",
                    value=str(note[0])
                )
            )

        super().__init__(
            placeholder="Select note",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        note_id = int(self.values[0])

        notes_service.toggle_status(note_id)

        note = notes_service.get_note(note_id)
        notes = notes_service.get_user_notes(interaction.user.id)

        await interaction.response.edit_message(
            content=f"Status changed to **{note[5]}**\n\n{format_notes_list(notes)}",
            view=None
        )
    
class DeleteNoteDropdown(discord.ui.Select):

    def __init__(self, notes):

        options = []

        for note in notes:
            options.append(
                discord.SelectOption(
                    label=note[1],
                    description=f"Status: {note[5]}",
                    value=str(note[0])
                )
            )

        super().__init__(
            placeholder="Select note to delete",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        note_id = int(self.values[0])
        note = notes_service.get_note(note_id)

        view = ConfirmDeleteView(note_id)

        await interaction.response.edit_message(
            content=f"Delete **{note[1]}**? This cannot be undone.",
            view=view
        )
        view.message = interaction.message

class ConfirmDeleteButton(discord.ui.Button):

    def __init__(self, note_id):
        super().__init__(
            label="Delete",
            style=discord.ButtonStyle.red
        )

        self.note_id = note_id

    async def callback(self, interaction: discord.Interaction):

        notes_service.delete_note(self.note_id)

        notes = notes_service.get_user_notes(interaction.user.id)

        await interaction.response.edit_message(
            content=f"Note deleted 🗑️\n\n{format_notes_list(notes)}",
            view=None
        )

class CancelDeleteButton(discord.ui.Button):

    def __init__(self, note_id):
        super().__init__(
            label="Cancel",
            style=discord.ButtonStyle.gray
        )

        self.note_id = note_id

    async def callback(self, interaction: discord.Interaction):

        await interaction.response.edit_message(
            content="Deletion cancelled",
            view=None
        )

class ConfirmDeleteView(SelfCleaningView):

    def __init__(self, note_id):
        super().__init__(timeout=60)

        self.add_item(ConfirmDeleteButton(note_id))
        self.add_item(CancelDeleteButton(note_id))

class EditNoteView(SelfCleaningView):

    def __init__(self, notes):
        super().__init__(timeout=120)

        self.add_item(EditNoteDropdown(notes))

class StatusNoteView(SelfCleaningView):

    def __init__(self, notes):
        super().__init__(timeout=120)

        self.add_item(StatusNoteDropdown(notes))

class DeleteNoteView(SelfCleaningView):

    def __init__(self, notes):
        super().__init__(timeout=120)

        self.add_item(DeleteNoteDropdown(notes))

class ApproveButton(discord.ui.Button):

    def __init__(self, note_id):
        super().__init__(
            label="Approve",
            style=discord.ButtonStyle.green
        )

        self.note_id = note_id

    async def callback(self, interaction: discord.Interaction):

        notes_service.toggle_status(self.note_id)

        notes = notes_service.get_user_notes(interaction.user.id)

        await interaction.response.edit_message(
            content=f"Note approved ✅\n\n{format_notes_list(notes)}",
            view=None
        )

class KeepDraftButton(discord.ui.Button):

    def __init__(self, note_id):
        super().__init__(
            label="Keep as Draft",
            style=discord.ButtonStyle.gray
        )

        self.note_id = note_id

    async def callback(self, interaction: discord.Interaction):

        notes = notes_service.get_user_notes(interaction.user.id)

        await interaction.response.edit_message(
            content=f"Note saved as draft 📝\n\n{format_notes_list(notes)}",
            view=None
        )

class ApproveDraftView(SelfCleaningView):

    def __init__(self, note_id):
        super().__init__(timeout=120)

        self.add_item(ApproveButton(note_id))
        self.add_item(KeepDraftButton(note_id))

class CreateButton(discord.ui.Button):

    def __init__(self):
        super().__init__(
            label="Create Note",
            style=discord.ButtonStyle.green
        )

    async def callback(self, interaction: discord.Interaction):

        modal = CreateNoteModal()
        await interaction.response.send_modal(modal)
        await interaction.message.delete()

class EditButton(discord.ui.Button):

    def __init__(self, notes):
        super().__init__(
            label="Edit Note",
            style=discord.ButtonStyle.blurple
        )

        self.notes = notes

    async def callback(self, interaction: discord.Interaction):

        view = EditNoteView(self.notes)

        await interaction.response.send_message(
            "Select a note to edit:",
            view=view,
            ephemeral=True
        )
        view.message = await interaction.original_response()
        await interaction.message.delete()

class DeleteButton(discord.ui.Button):

    def __init__(self, notes):
        super().__init__(
            label="Delete Note",
            style=discord.ButtonStyle.red
        )

        self.notes = notes

    async def callback(self, interaction: discord.Interaction):

        view = DeleteNoteView(self.notes)

        await interaction.response.send_message(
            "Select a note to delete:",
            view=view,
            ephemeral=True
        )
        view.message = await interaction.original_response()
        await interaction.message.delete()

class StatusButton(discord.ui.Button):

    def __init__(self, notes):
        super().__init__(
            label="Change Note Status",
            style=discord.ButtonStyle.gray
        )

        self.notes = notes

    async def callback(self, interaction: discord.Interaction):

        view = StatusNoteView(self.notes)

        await interaction.response.send_message(
            "Select a note:",
            view=view,
            ephemeral=True
        )
        view.message = await interaction.original_response()
        await interaction.message.delete()


class ApproveAllButton(discord.ui.Button):

    def __init__(self):
        super().__init__(
            label="Approve All Notes",
            style=discord.ButtonStyle.green
        )

    async def callback(self, interaction: discord.Interaction):

        notes_service.approve_all_notes(interaction.user.id)

        notes = notes_service.get_user_notes(interaction.user.id)

        await interaction.response.send_message(
            f"All drafts have been approved ✅\n\n{format_notes_list(notes)}",
            ephemeral=True
        )
        await interaction.message.delete()

class CreateMenuView(SelfCleaningView):

    def __init__(self, notes):
        super().__init__(timeout=180)
        self.notes = notes

        self.add_item(CreateButton())

        if notes:
            self.add_item(EditButton(notes))
            self.add_item(StatusButton(notes))
            self.add_item(DeleteButton(notes))

            if any(note[5] == "draft" for note in notes):
                self.add_item(ApproveAllButton())

class Notes(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def note(self, ctx):

        user_notes = notes_service.get_user_notes(ctx.author.id)

        message = format_notes_list(user_notes)

        view = CreateMenuView(user_notes)

        sent_message = await ctx.send(message, view=view, ephemeral=True)
        view.message = sent_message
        
async def setup(bot):
    await bot.add_cog(Notes(bot))