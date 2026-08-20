from config import BOT_ADMIN_ROLE_ID, TEAM_LEAD_ROLE_ID, MEMBER_ROLE_ID

def has_role(member, role_id):
    return any(str(role.id) == role_id for role in member.roles)

def is_bot_admin(member):
    return has_role(member, BOT_ADMIN_ROLE_ID)

def is_team_lead(member):
    return (
        has_role(member, TEAM_LEAD_ROLE_ID)
        or is_bot_admin(member)
    )

def is_member(member):
    return (
        has_role(member, MEMBER_ROLE_ID)
        or is_team_lead(member)
    )




