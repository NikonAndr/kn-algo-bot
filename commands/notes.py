import discord
from discord.ext import commands
from services import notes_service

class CreateNoteModal(discord.ui.Modal, title="Create Weekly Note"):

    title_input = discord.ui.TextInput(
        label="Title",
        max_length=100
    )

    content_input = discord.ui.TextInput(
        label="Content",
        style=discord.TextStyle.paragraph,
        max_length=2000
    )

    async def on_submit(self, interaction: discord.Interaction):
        print("DISPLAY:", interaction.user.display_name)
        print("USERNAME:", interaction.user.name)
        print("NICK:", interaction.user.nick)

        title = self.title_input.value
        content = self.content_input.value

        author_id = interaction.user.id
        author_name = interaction.user.display_name

        notes_service.create_note(title, content, author_id, author_name)

        await interaction.response.send_message("Note Created!", ephemeral=True)

class EditNoteModal(discord.ui.Modal, title="Edit Note"):

    def __init__(self, note):

        super().__init__()

        self.note_id = note[0]

        self.title_input = discord.ui.TextInput(
            label="Title",
            default=note[1],
            max_length=100
        )

        self.content_input = discord.ui.TextInput(
            label="Content",
            default=note[2],
            style=discord.TextStyle.paragraph,
            max_length=2000
        )

        self.add_item(self.title_input)
        self.add_item(self.content_input)

    async def on_submit(self, interaction: discord.Interaction):

        notes_service.edit_note(
            self.note_id,
            self.title_input.value,
            self.content_input.value
        )

        await interaction.response.send_message(
            "Note updated!",
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

        await interaction.response.send_message(
            f"Status changed to **{note[5]}**",
            ephemeral=True
        )
    
class EditNoteView(discord.ui.View):

    def __init__(self, notes):
        super().__init__(timeout=120)

        self.add_item(EditNoteDropdown(notes))

class StatusNoteView(discord.ui.View):

    def __init__(self, notes):
        super().__init__(timeout=120)

        self.add_item(StatusNoteDropdown(notes))
        
class CreateButton(discord.ui.Button):

    def __init__(self):
        super().__init__(
            label="Create Note",
            style=discord.ButtonStyle.green
        )

    async def callback(self, interaction: discord.Interaction):

        modal = CreateNoteModal()
        await interaction.response.send_modal(modal)

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


class CreateMenuView(discord.ui.View):

    def __init__(self, notes):
        super().__init__(timeout=180)
        self.notes = notes

        self.add_item(CreateButton())

        if notes:
            self.add_item(EditButton(notes))
            self.add_item(StatusButton(notes))

class Notes(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def note(self, ctx):

        user_notes = notes_service.get_user_notes(ctx.author.id)
        
        if not user_notes:
            message = "You don't have any notes yet."
        else:

            message = "Your Notes\n"

            for note in user_notes:
                message += f"- {note[1]} ({note[5]})\n"
            
        view = CreateMenuView(user_notes)
            
        await ctx.send(message, view=view, ephemeral=True)
        
async def setup(bot):
    await bot.add_cog(Notes(bot))