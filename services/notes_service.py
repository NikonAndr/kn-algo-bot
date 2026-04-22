from database import weekly_notes

def create_note(title, content, author_id, author_name):
    weekly_notes.create_note(title, content, author_id, author_name)

def get_user_notes(author_id):
    return weekly_notes.get_notes_by_author(author_id)

def get_note(note_id):
    return weekly_notes.get_note(note_id)

def edit_note(note_id, title, content):

    note = weekly_notes.get_note(note_id)

    if not note:
        return False

    weekly_notes.update_note(note_id, title, content)

    return True

def toggle_status(note_id):

    note = weekly_notes.get_note(note_id)

    if not note :
        return False
    
    status = note[5]

    if status == "sent":
        return False

    if status == "draft":
        new_status = "approved"
    else:
        new_status = "draft"

    weekly_notes.set_status(note_id, new_status)

    return new_status

def get_notes_to_send():
    return weekly_notes.get_approved_notes()

def mark_notes_sent(notes):
    
    for note in notes:
        weekly_notes.set_status(note[0], "sent")

def get_draft_notes():
    return weekly_notes.get_draft_notes()