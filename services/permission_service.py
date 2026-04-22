from config import BOT_ADMIN_ROLE_ID, BOT_NOTES_ROLE_ID, MEMBER_ROLE_ID

def has_role(member, role_id):
    return any(str(role.id) == role_id for role in member.roles)        

def is_bot_admin(member):
    return has_role(member, BOT_ADMIN_ROLE_ID)

def can_manage_notes(member):
    return (
        has_role(member, BOT_NOTES_ROLE_ID)
        or is_bot_admin(member)
    )

def is_member(member):
    return (
        has_role(member, MEMBER_ROLE_ID)
        or can_manage_notes(member)
    )




