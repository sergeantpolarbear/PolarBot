import asyncio

from discord.ext import commands

hybrid_command = getattr(commands, "hybrid_command", commands.command)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @hybrid_command(name="warn", description="Warn a player via PolarBridge")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, player: str, *, reason: str = "No reason provided"):
        payload = {"action": "warn", "player": player, "reason": reason}
        await asyncio.to_thread(self.bot.polar_link.send, "polarbridge", "bridge.mod", payload)
        await ctx.reply(f"Warned {player}")

    @hybrid_command(name="kick", description="Kick a player via PolarBridge")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, player: str, *, reason: str = "No reason provided"):
        payload = {"action": "kick", "player": player, "reason": reason}
        await asyncio.to_thread(self.bot.polar_link.send, "polarbridge", "bridge.mod", payload)
        await ctx.reply(f"Kicked {player}")

    @hybrid_command(name="ban", description="Ban a player via PolarBridge")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, player: str, *, reason: str = "No reason provided"):
        payload = {"action": "ban", "player": player, "reason": reason}
        await asyncio.to_thread(self.bot.polar_link.send, "polarbridge", "bridge.mod", payload)
        await ctx.reply(f"Banned {player}")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
