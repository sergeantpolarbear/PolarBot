import asyncio

from discord.ext import commands

hybrid_command = getattr(commands, "hybrid_command", commands.command)


class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @hybrid_command(name="registerrelay", description="Register this bot in the relay registry")
    @commands.is_owner()
    async def registerrelay(self, ctx):
        response = await asyncio.to_thread(self.bot.polar_link.register)
        await ctx.reply(f"Relay register: {response}")

    @hybrid_command(name="reloadcogs", description="Reload bot cogs")
    @commands.is_owner()
    async def reloadcogs(self, ctx):
        for extension in list(self.bot.extensions):
            await self.bot.reload_extension(extension)
        await ctx.reply("Cogs reloaded.")


async def setup(bot):
    await bot.add_cog(BotCommands(bot))
