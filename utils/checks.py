from discord.ext import commands
from services import permission_service

def bot_admin_only():
    async def predicate(ctx):
        return permission_service.is_bot_admin(ctx.author)
    
    return commands.check(predicate)

def team_lead_only():
    async def predicate(ctx):
        return permission_service.is_team_lead(ctx.author)

    return commands.check(predicate)

def member_only():
    async def predicate(ctx):
        return permission_service.is_member(ctx.author)
    
    return commands.check(predicate)