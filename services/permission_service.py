from config import BOT_ADMIN_ROLE_ID, MANAGEMENT_ROLE_ID, MEMBER_ROLE_ID, SUPERVISOR_ROLE_ID

def has_role(member, role_id):
    return any(str(role.id) == role_id for role in member.roles)

def is_bot_admin(member):
    return has_role(member, BOT_ADMIN_ROLE_ID)

def is_management(member):
    return (
        has_role(member, MANAGEMENT_ROLE_ID)
        or is_bot_admin(member)
    )

def is_member(member):
    return (
        has_role(member, MEMBER_ROLE_ID)
        or has_role(member, SUPERVISOR_ROLE_ID)
        or is_management(member)
    )




