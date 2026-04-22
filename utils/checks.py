from discord.ext import commands
from services import permission_service

def bot_admin_only():
    async def predicate(ctx):
        return permission_service.is_bot_admin(ctx.author)
    
    return commands.check(predicate)

def notes_manager_only():
    async def predicate(ctx):
        return permission_service.can_manage_notes(ctx.author)
    
    return commands.check(predicate)

def member_only():
    async def predicate(ctx):
        return permission_service.is_member(ctx.author)
    
    return commands.check(predicate)