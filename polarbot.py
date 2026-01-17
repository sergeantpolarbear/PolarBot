import logging
import os
import sys
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if sys.path and os.path.abspath(sys.path[0]) == SCRIPT_DIR:
    sys.path.pop(0)

import discord
from discord.ext import commands
from dotenv import load_dotenv

from polarlink.polarlink import PolarLink


load_dotenv()

TOKEN = os.getenv("TOKEN")


def _parse_id_set(value: str) -> set:
    ids = set()
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            ids.add(int(raw))
        except ValueError:
            logging.warning("Ignoring non-numeric ID in env: %s", raw)
    return ids


DEVS = _parse_id_set(os.getenv("DEVS", ""))
OWNERS = _parse_id_set(os.getenv("OWNERS", ""))


def _discover_extensions():
    cogs_dir = Path(ROOT_DIR) / "polarbot" / "cogs"
    if not cogs_dir.exists():
        return []
    extensions = []
    for path in sorted(cogs_dir.glob("*.py")):
        if path.name.startswith("_") or path.name == "__init__.py":
            continue
        extensions.append(f"polarbot.cogs.{path.stem}")
    return extensions


def _resolve_extensions():
    raw = os.getenv("POLAR_COGS", "").strip()
    if not raw:
        return _discover_extensions()
    extensions = []
    for item in raw.split(","):
        name = item.strip()
        if not name:
            continue
        if name.startswith("polarbot."):
            extensions.append(name)
        else:
            extensions.append(f"polarbot.cogs.{name}")
    return extensions


class PolarBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix=("pb>", "pba>", "pbd>", "pbo>"),
            intents=intents,
            owner_ids=OWNERS or None,
        )
        self.polar_link = PolarLink(role="polarbot")

    async def setup_hook(self):
        for extension in _resolve_extensions():
            try:
                await self.load_extension(extension)
            except Exception:
                logging.exception("Failed to load extension: %s", extension)
        if hasattr(self, "tree"):
            try:
                synced = await self.tree.sync()
                logging.info("Synced %s commands", len(synced))
            except Exception:
                logging.exception("Command sync failed")


def is_dev():
    async def predicate(ctx):
        return ctx.author.id in DEVS or await ctx.bot.is_owner(ctx.author)

    return commands.check(predicate)


bot = PolarBot()


@bot.event
async def on_ready():
    logging.info("Logged in as %s (id: %s)", bot.user, bot.user.id)


@bot.event
async def on_error(event, *args, **kwargs):
    logging.exception("Unhandled error in event: %s", event)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.reply("You do not have permission to use that command.")
        return
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"Command is on cooldown: {error.retry_after:.1f}s")
        return
    logging.exception("Command error", exc_info=error)
    await ctx.reply("Command failed. Check logs for details.")


if hasattr(bot, "tree"):
    @bot.tree.error
    async def on_app_command_error(
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ):
        logging.exception("App command error", exc_info=error)
        if interaction.response.is_done():
            await interaction.followup.send("Command failed. Check logs for details.", ephemeral=True)
        else:
            await interaction.response.send_message("Command failed. Check logs for details.", ephemeral=True)


@bot.command(name="devping")
@is_dev()
async def devping(ctx):
    await ctx.reply(f"Pong! (dev prefix via {ctx.prefix})")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not TOKEN:
        raise SystemExit("TOKEN is not set")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
