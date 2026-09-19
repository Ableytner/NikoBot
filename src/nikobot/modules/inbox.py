"""HTTP inbox module for receiving messages from AblApi

Example message:
{
    "title": "Build Notification",
    "message": "Build #42 completed successfully.",
    "channel_id": "123456789012345678",
    "color": "3447003",
    "fields": [
        {"name": "Branch", "value": "main", "inline": true},
        {"name": "Duration", "value": "2m 14s", "inline": true}
    ]
}
"""

# pylint: disable=broad-exception-caught

import asyncio
import json
import logging

from abllib import VolatileStorage
from abllib.log import get_logger, LogLevel
from aiohttp import web
import discord as discordpy
from discord.ext import commands

from nikobot.util import discord

logger = get_logger("inbox")

PORT: int = 8888

class InboxHandler:
    """Handles incoming HTTP requests from AblApi"""

    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot
        self._runner: web.AppRunner | None = None

    async def handle_post(self, request: web.Request) -> web.Response:
        """Handle incoming POST requests from AblApi"""

        logger.debug(f"Got request: {await request.text()}")

        response = await self._validate_request(request)
        if response is not None:
            return response

        future = asyncio.get_event_loop().create_future()

        async def send_and_resolve():
            msg = await self._send_message(await request.json())
            if msg is None:
                future.set_result({"status": "failed", "reason": "Could not send message to Discord"})
                return
            future.set_result({
                "status": "success",
                "message_id": str(msg.id),
                "channel_id": str(msg.channel.id)
            })

        asyncio.ensure_future(send_and_resolve())

        try:
            result = await asyncio.wait_for(future, timeout=30.0)
            return web.json_response(result, status=200)
        except asyncio.TimeoutError:
            return web.Response(
                status=504,
                text="Gateway Timeout",
                content_type="text/plain"
            )

    async def _validate_request(self, request: web.Request) -> web.Response | None:
        """Ensure the request is not malformed"""

        if not await self._check_auth(request):
            logger.warning("Unauthorized access attempt")
            return web.Response(
                status=401,
                text="Unauthorized",
                content_type="text/plain"
            )

        try:
            body = await request.json()
        except json.JSONDecodeError:
            return web.Response(
                status=400,
                text="Invalid JSON",
                content_type="text/plain"
            )

        if not isinstance(body, dict):
            return web.Response(
                status=400,
                text="Expected JSON object",
                content_type="text/plain"
            )

        if "title" not in body:
            return web.Response(
                status=400,
                text="Missing required field: title",
                content_type="text/plain"
            )

        if "message" not in body:
            return web.Response(
                status=400,
                text="Missing required field: message",
                content_type="text/plain"
            )

        # no complaints
        return None

    async def _check_auth(self, request: web.Request) -> bool:
        """Check if the request has a valid API secret"""

        provided_secret = request.headers.get("X-Api-Secret", "")
        expected_secret = VolatileStorage["inbox.api_secret"]
        return provided_secret == expected_secret

    async def _send_message(self, data: dict) -> discordpy.Message | None:
        """Send a Discord message from the received data"""

        title = data.get("title", "AblApi Notification")
        message = data.get("message", "")
        color = data.get("color", discordpy.Color.blue())

        if isinstance(color, str):
            try:
                color = int(color, 16)
            except ValueError:
                color = discordpy.Color.blue()

        embed = discordpy.Embed(title=title, description=message, color=color)

        fields = data.get("fields", [])
        for field in fields:
            if isinstance(field, dict):
                name = field.get("name", "")
                value = field.get("value", "")
                inline = field.get("inline", False)
                embed.add_field(name=name, value=value, inline=inline)

        channel_id = data["channel_id"]

        if channel_id == "owner":
            try:
                return await discord.private_message(discord.get_owner_id(), embed=embed)
            except Exception:
                logger.exception("Failed to send inbox message to owner")
                return None

        try:
            channel_id = int(channel_id)

            allowed_channels = VolatileStorage["inbox.allowed_channels"]
            if allowed_channels and channel_id not in allowed_channels:
                logger.warning(f"Channel {channel_id} not in allowed_channels")
                return None

            return await discord.channel_message(channel_id, embed=embed)
        except Exception:
            logger.exception("Failed to send inbox message")
            return None

    async def start(self) -> None:
        """Start the HTTP server"""

        # shut up logger
        server_logger = logging.getLogger("aiohttp.server")
        server_logger.setLevel(LogLevel.WARNING.value)
        access_logger = logging.getLogger("aiohttp.access")
        access_logger.setLevel(LogLevel.WARNING.value)

        app = web.Application()
        app.router.add_post("/api/inbox", self.handle_post)

        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, "0.0.0.0", PORT)
        await site.start()

        logger.info(f"Inbox HTTP server listening on 0.0.0.0:{PORT}")

    async def stop(self) -> None:
        """Stop the HTTP server"""
        if self._runner:
            await self._runner.cleanup()
            logger.info("Inbox HTTP server stopped")

async def setup(bot) -> None:
    """Setup the inbox module"""

    handler = InboxHandler(bot)

    try:
        await handler.start()
    except Exception:
        logger.exception("Failed to start inbox HTTP server")
