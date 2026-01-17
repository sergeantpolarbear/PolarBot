import asyncio
import os
import re
import logging

from discord.ext import commands


class LiveChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bridge_channel_id = self._parse_channel_id("POLAR_BRIDGE_CHANNEL_ID")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not self.bridge_channel_id or message.channel.id != self.bridge_channel_id:
            return
        payload = {
            "author": str(message.author),
            "content": message.content,
            "channel": message.channel.id,
        }
        await asyncio.to_thread(self.bot.polar_link.send, "polarbridge", "bridge.chat", payload)

    def _parse_channel_id(self, env_name):
        raw = os.getenv(env_name, "").strip()
        if not raw:
            return 0
        match = re.search(r"(\\d+)", raw)
        if not match:
            logging.warning("Invalid channel ID in %s", env_name)
            return 0
        return int(match.group(1))


async def setup(bot):
    await bot.add_cog(LiveChat(bot))
