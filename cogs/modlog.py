import asyncio

from discord.ext import commands


class ModLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_action(self, action, actor, target=None, reason=None):
        payload = {
            "action": action,
            "actor": actor,
            "target": target,
            "reason": reason,
        }
        await asyncio.to_thread(self.bot.polar_link.send, "polarbot", "modlog", payload)


async def setup(bot):
    await bot.add_cog(ModLog(bot))
