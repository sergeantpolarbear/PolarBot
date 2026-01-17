from discord.ext import commands

hybrid_command = getattr(commands, "hybrid_command", commands.command)


class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @hybrid_command(name="relaystatus", description="Shows relay connectivity")
    async def relaystatus(self, ctx):
        link = self.bot.polar_link
        await ctx.reply(
            f"Relay: {link.client.relay_url}\nSID: {link.identity.sid}\nRole: {link.identity.role}"
        )


async def setup(bot):
    await bot.add_cog(Status(bot))
