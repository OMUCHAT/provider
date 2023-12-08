from __future__ import annotations

import datetime
import json
import re
import time
from typing import Dict, List

import websockets
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

from ...provider import ProviderService
from ...tasks import Tasks
from .types import api, events

INFO = Provider(
    id="misskey",
    url="misskey-hub.net",
    name="Misskey",
    version="0.0.1",
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
    def __init__(self, host: str, meta: api.Meta, emojis: api.Emojis):
        self.host = host
        self.meta = meta
        self.emojis: Dict[str, str] = {
            emoji["name"]: emoji["url"] for emoji in emojis["emojis"]
        }
        self.user_details: Dict[str, api.UserDetail] = {}

    @classmethod
    async def create(cls, host: str) -> MisskeyInstance:
        meta = await cls.fetch_meta(host)
        emojis = await cls.fetch_emojis(host)
        return cls(host, meta, emojis)

    @classmethod
    async def fetch_meta(cls, host: str) -> api.Meta:
        res = await session.post(f"https://{host}/api/meta", json={"detail": True})
        return await res.json()

    @classmethod
    async def fetch_emojis(cls, host: str) -> api.Emojis:
        res = await session.get(f"https://{host}/api/emojis")
        return await res.json()

    async def fetch_user_detail(self, user_id: str) -> api.UserDetail:
        if user_id in self.user_details:
            return self.user_details[user_id]
        res = await session.post(
            f"https://{self.host}/api/users/show", json={"userId": user_id}
        )
        data: api.UserDetail = await res.json()
        self.user_details[user_id] = data
        return data


class MisskeyRoomService:
    def __init__(
        self,
        client: Client,
        channel: Channel,
        room: Room,
        socket: websockets.WebSocketClientProtocol,
        instance: MisskeyInstance,
    ):
        self.client = client
        self.channel = channel
        self.room = room
        self.socket = socket
        self.instance = instance
        self.tasks = Tasks(client.loop)

    @classmethod
    async def create(
        cls, client: Client, channel: Channel, host: str, channel_id: str | None = None
    ):
        instance = await MisskeyInstance.create(host)
        socket = await websockets.connect(
            f"wss://{host}/streaming?_t={time.time() * 1000}",
            ping_interval=None,
        )
        await socket.send(
            json.dumps(
                {
                    "type": "connect",
                    "body": {
                        "channel": "localTimeline",
                        "id": "2",
                        "params": {"withReplies": False},
                    },
                }
            )
        )
        room = Room(
            id=channel_id or "homeTimeline",
            provider_id=INFO.key(),
            channel_id=channel_id,
            name=f"Misskey {channel_id or 'homeTimeline'}",
            online=True,
            url=f"https://{host}/",
        )
        await client.rooms.add(room)

        self = cls(client, channel, room, socket, instance)
        self.tasks.create_task(self.start())
        return self

    def _parse_message_text(self, text: str) -> RootContent:
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

    async def fetch_user_roles(self, user_id: str) -> List[Role]:
        data = await self.instance.fetch_user_detail(user_id)
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
        return roles

    async def start(self):
        while True:
            message = await self.socket.recv()
            data = json.loads(message)
            if event := events.Channel(data):
                note = event["body"]
                if not note["text"]:
                    continue
                user = note["user"]
                roles = await self.fetch_user_roles(user["id"])
                author = Author(
                    id=user["id"],
                    name=user["name"],
                    avatar_url=user["avatarUrl"],
                    roles=roles,
                )
                message = Message(
                    room_id=self.channel.id,
                    id=f"test-{time.time_ns()}",
                    content=self._parse_message_text(note.get("text", None)),
                    author=author,
                    created_at=datetime.datetime.now(),
                )
                await self.client.messages.add(message)

    async def stop(self):
        self.tasks.terminate()
        await self.client.rooms.remove(self.room)
