import asyncio
import json
import os
import re
import logging

from discord.ext import commands, tasks

hybrid_command = getattr(commands, "hybrid_command", commands.command)


class RelayLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link = bot.polar_link
        self.log_channel_id = self._parse_channel_id("POLAR_LOG_CHANNEL_ID")
        self.bridge_channel_id = self._parse_channel_id("POLAR_BRIDGE_CHANNEL_ID")
        self.manager_channel_id = self._parse_channel_id("POLAR_MANAGER_CHANNEL_ID")
        self.poll_relay.start()

    def cog_unload(self):
        self.poll_relay.cancel()

    async def _send_to_channel(self, channel_id, content):
        if not channel_id:
            return
        channel = self.bot.get_channel(channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception:
                logging.warning("Unable to fetch channel %s", channel_id)
                return
        await channel.send(content)

    def _parse_channel_id(self, env_name):
        raw = os.getenv(env_name, "").strip()
        if not raw:
            return 0
        match = re.search(r"(\\d+)", raw)
        if not match:
            logging.warning("Invalid channel ID in %s", env_name)
            return 0
        return int(match.group(1))

    async def handle_message(self, message):
        kind = message.get("kind", "event")
        payload = message.get("payload", {})
        meta = message.get("meta", {})

        if kind == "log":
            level = payload.get("level", "INFO")
            text = payload.get("message", "")
            await self._send_to_channel(self.log_channel_id, f"[{level}] {text}")
        elif kind == "bridge.chat":
            author = payload.get("author", "unknown")
            text = payload.get("content", "")
            await self._send_to_channel(self.bridge_channel_id, f"[MC] {author}: {text}")
        elif kind == "bridge.join":
            player = payload.get("player", "unknown")
            await self._send_to_channel(self.bridge_channel_id, f"[MC] {player} joined")
        elif kind == "bridge.leave":
            player = payload.get("player", "unknown")
            await self._send_to_channel(self.bridge_channel_id, f"[MC] {player} left")
        elif kind == "bridge.death":
            player = payload.get("player", "unknown")
            await self._send_to_channel(self.bridge_channel_id, f"[MC] {player} died")
        elif kind == "manager.event":
            action = payload.get("action", "event")
            component = payload.get("component", "unknown")
            await self._send_to_channel(
                self.manager_channel_id,
                f"[Manager] {action} {component}",
            )

        destination = meta.get("original_destination")
        if destination:
            forward_meta = dict(meta)
            forward_meta.pop("original_destination", None)
            forward_meta["forwarded_by"] = "polarbot"
            await asyncio.to_thread(self.link.send, destination, kind, payload, forward_meta)

    @tasks.loop(seconds=1.0)
    async def poll_relay(self):
        try:
            messages = await asyncio.to_thread(self.link.pull, "polarbot")
        except Exception:
            return
        for message in messages:
            try:
                await self.handle_message(message)
            except Exception:
                logging.exception("Failed to handle relay message")

    @poll_relay.before_loop
    async def before_poll_relay(self):
        await self.bot.wait_until_ready()

    @hybrid_command(name="relay", description="Send a relay message")
    async def relay(self, ctx, destination: str, kind: str, *, payload: str = "{}"):
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            await ctx.reply("Payload must be JSON.")
            return
        await asyncio.to_thread(
            self.link.send,
            destination,
            kind,
            data,
            {"sender": str(ctx.author)},
        )
        await ctx.reply("Relay message sent.")


async def setup(bot):
    await bot.add_cog(RelayLink(bot))
