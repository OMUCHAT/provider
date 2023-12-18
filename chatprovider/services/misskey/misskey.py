from __future__ import annotations

import asyncio
import datetime
import json
import re
import time
from typing import Dict, List

from loguru import logger
from omuchat import ImageContent, Role
from omuchat.client import Client
from omuchat.model import (
    Author,
    Channel,
    Message,
    Provider,
    Room,
    RootContent,
    TextContent,
)
from websockets import client, exceptions

from ...provider import ProviderService
from ...tasks import Tasks
from .types import api, events

INFO = Provider(
    id="misskey",
    url="misskey-hub.net",
    name="Misskey",
    version="0.1.0",
    repository_url="https://github.com/OMUCHAT/provider",
    description="Misskey provider",
    regex=r"(?P<host>[\w\.]+\.\w+)(/channels/(?P<channel>[^/]+))?/?",
)
session = INFO.get_session()


class MisskeyService(ProviderService):
    def __init__(self, client: Client):
        self.client = client
        self.rooms: dict[str, MisskeyRoomService] = {}

    @property
    def info(self) -> Provider:
        return INFO

    async def start_channel(self, channel: Channel):
        if channel.url in self.rooms:
            return
        match = re.match(INFO.regex, channel.url)
        if match is None:
            return
        options = match.groupdict()
        room = await MisskeyRoomService.create(
            self.client, channel, options["host"], options["channel"]
        )
        self.rooms[channel.url] = room

    async def stop_channel(self, channel: Channel):
        if channel.url not in self.rooms:
            return
        room = self.rooms[channel.url]
        await room.stop()
        del self.rooms[channel.url]


class MisskeyInstance:
    def __init__(self, client: Client, host: str, meta: api.Meta, emojis: api.Emojis):
        self.client = client
        self.host = host
        self.meta = meta
        _emojis = {emoji["name"]: emoji["url"] for emoji in emojis["emojis"]}
        self.emojis: Dict[str, str] = {
            k: _emojis[k] for k in sorted(_emojis, key=lambda k: len(k), reverse=True)
        }
        self.user_details: Dict[str, Author] = {}

    @classmethod
    async def create(cls, client: Client, host: str) -> MisskeyInstance:
        meta = await cls.fetch_meta(host)
        emojis = await cls.fetch_emojis(host)
        return cls(client, host, meta, emojis)

    @classmethod
    async def fetch_meta(cls, host: str) -> api.Meta:
        res = await session.post(f"https://{host}/api/meta", json={"detail": True})
        return await res.json()

    @classmethod
    async def fetch_emojis(cls, host: str) -> api.Emojis:
        res = await session.get(f"https://{host}/api/emojis")
        return await res.json()

    async def fetch_author(self, user_id: str) -> Author:
        if user_id in self.user_details:
            return self.user_details[user_id]
        if author := await self.client.authors.get(f"{INFO.id}:{user_id}"):
            return author
        res = await session.post(
            f"https://{self.host}/api/users/show", json={"userId": user_id}
        )
        res.raise_for_status()
        data: api.UserDetail = await res.json()
        roles: List[Role] = []
        for role in sorted(data["roles"], key=lambda r: r["displayOrder"]):
            roles.append(
                Role(
                    id=role["name"],
                    name=role["name"],
                    icon_url=role["iconUrl"],
                    color=role["color"],
                    is_owner=role["isAdministrator"],
                    is_moderator=role["isModerator"],
                )
            )
        author = Author(
            provider_id=INFO.id,
            id=data["id"],
            name=data["name"],
            avatar_url=data["avatarUrl"],
            roles=roles,
        )
        await self.client.authors.add(author)
        self.user_details[user_id] = author
        return author


class MisskeyRoomService:
    def __init__(
        self,
        client: Client,
        channel: Channel,
        room: Room,
        instance: MisskeyInstance,
    ):
        self.client = client
        self.channel = channel
        self.room = room
        self.instance = instance
        self.tasks = Tasks(client.loop)

    @classmethod
    async def create(
        cls, client: Client, channel: Channel, host: str, channel_id: str | None = None
    ):
        instance = await MisskeyInstance.create(client, host)
        room = Room(
            id=channel_id or "homeTimeline",
            provider_id=INFO.key(),
            channel_id=channel_id,
            name=f"Misskey {channel_id or 'homeTimeline'}",
            online=False,
            url=f"https://{host}/",
        )
        await client.rooms.add(room)

        self = cls(client, channel, room, instance)
        self.tasks.create_task(self.start())
        return self

    def _parse_message_text(self, text: str | None) -> RootContent:
        if text is None:
            return RootContent.empty()
        root = RootContent()
        regex = re.compile(r":(\w+):")
        emojis = self.instance.emojis
        while True:
            match = regex.search(text)
            if match is None:
                break
            emoji_name = match.group(1)
            root.add(TextContent.of(text[: match.start()]))
            if emoji_name in emojis:
                root.add(ImageContent.of(url=emojis[emoji_name], id=emoji_name))
            else:
                root.add(TextContent.of(f":{emoji_name}:"))
            text = text[match.end() :]
        root.add(TextContent.of(text))
        return root

    async def start(self):
        while True:
            try:
                socket = await self.create_socket()
                await self.connect(socket)
                self.room.online = True
                await self.client.rooms.update(self.room)
                await self.listen(socket)
            except exceptions.ConnectionClosed:
                logger.warning("Misskey socket closed")
                continue
            self.room.online = False
            await self.client.rooms.update(self.room)

    async def create_socket(self):
        socket = await client.connect(
            f"wss://{self.instance.host}/streaming?_t={time.time() * 1000}&i=Ea7ZpQdHnO8LISib",
            extra_headers=session.headers,
        )
        return socket

    async def connect(self, socket: client.WebSocketClientProtocol):
        await socket.send(
            events.Connect.json(
                {
                    "channel": "localTimeline",
                    "id": self.room.key(),
                    "params": {
                        "withRenotes": True,
                        "withReplies": True,
                    },
                }
            )
        )

    async def listen(self, socket: client.WebSocketClientProtocol):
        while True:
            message = await socket.recv()
            data = json.loads(message)
            if event := self.validate_event(data):
                await self.process_message(event)

    async def ping(self, socket):
        while True:
            await socket.send("h")
            await asyncio.sleep(30)

    def validate_event(self, data: events.EventJson) -> events.EventJson | None:
        if "type" not in data:
            return None
        if "body" not in data:
            return None
        return data

    async def process_message(self, event_json: events.EventJson):
        if event := events.Channel(event_json):
            note = event["body"]
            if not note["text"]:
                return
            user = note["user"]
            author = await self.instance.fetch_author(user["id"])
            content = self._parse_message_text(note.get("text", None))
            created_at = datetime.datetime.fromisoformat(note["createdAt"][:-1])
            message = Message(
                id=note["id"],
                room_id=self.room.key(),
                content=content,
                author_id=author.key(),
                created_at=created_at,
            )
            await self.client.messages.add(message)

    async def stop(self):
        self.tasks.terminate()
        self.room.online = False
        await self.client.rooms.update(self.room)
