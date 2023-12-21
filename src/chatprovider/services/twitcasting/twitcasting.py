from __future__ import annotations

import random
import re
import string
import time
from datetime import datetime
from typing import List

import aiohttp
from aiohttp import web
from chatprovider.helper import HTTP_REGEX, get_session
from omuchat.client import Client
from omuchat.model import Channel, Message, Provider, Room
from omuchat.model.author import Author
from omuchat.model.content import TextContent
from omuchat.model.gift import Gift

from ...provider import ProviderService
from ...tasks import Tasks
from .token import get_session_id, get_token
from .types import api, events

INFO = Provider(
    id="twitcasting",
    url="twitcasting.tv",
    name="TwitCasting",
    version="0.1.0",
    repository_url="https://github.com/OMUCHAT/provider",
    description="TwitCasting provider",
    regex=HTTP_REGEX + r"twitcasting\.tv/(?P<user_id>[^/]+)",
)
session = get_session(INFO)


class TwitCastingService(ProviderService):
    def __init__(self, client: Client):
        self.client = client
        self.rooms: dict[str, TwitCastingRoomService] = {}

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
        room = await TwitCastingRoomService.create(
            self.client, channel, options["user_id"]
        )
        self.rooms[channel.url] = room

    async def stop_channel(self, channel: Channel):
        if channel.url not in self.rooms:
            return
        room = self.rooms[channel.url]
        await room.stop()
        del self.rooms[channel.url]


class TwitCastingChat:
    def __init__(self, user_id: str, movie_id: int, token: str):
        self.user_id = user_id
        self.movie_id = movie_id
        self.token = token

    @classmethod
    async def create(cls, user_id: str, movie_id: int):
        token = await get_token(
            movie_id,
            await get_session_id(f"https://twitcasting.tv/{user_id}"),
        )
        return cls(user_id, movie_id, token)

    @classmethod
    async def fetch_movie_id(cls, user_id: str) -> int:
        res = await session.get(
            "https://twitcasting.tv/streamserver.php",
            params={
                "target": user_id,
                "mode": "client",
                "player": "pc_web",
            },
        )
        data: api.StreamServer = await res.json()
        return data["movie"]["id"]

    async def fetch_ws(self) -> str:
        key = "WebKitFormBoundary" + "".join(
            random.choices(string.ascii_letters + string.digits, k=16)
        )
        n = int(time.time() * 1000)
        form_data = f"""------{key}
Content-Disposition: form-data; name="movie_id"

{self.movie_id}
------{key}
Content-Disposition: form-data; name="__n"

{n}
------{key}
Content-Disposition: form-data; name="password"


------{key}--"""
        res = await session.post(
            "https://twitcasting.tv/eventpubsuburl.php",
            data=form_data,
            headers={
                "Content-Type": f"multipart/form-data; boundary=----{key}",
            },
        )
        data: api.EventPubSubUrl = await res.json()
        return data["url"]


class TwitCastingRoomService:
    def __init__(
        self,
        client: Client,
        channel: Channel,
        room: Room,
        chat: TwitCastingChat,
    ):
        self.client = client
        self.channel = channel
        self.room = room
        self.chat = chat
        self.tasks = Tasks(client.loop)

    @classmethod
    async def create(cls, client: Client, channel: Channel, user_id: str):
        chat = await TwitCastingChat.create(
            user_id, await TwitCastingChat.fetch_movie_id(user_id)
        )
        room = Room(
            id=str(chat.movie_id),
            provider_id=INFO.key(),
            channel_id=channel.key(),
            image_url=f"https://twitcasting.tv/userajax.php?c=updateindexthumbnail&m={chat.movie_id}&u={chat.user_id}",
            name="",
            description="",
            online=False,
            url=f"https://twitcasting.tv/{chat.user_id}/movie/{chat.movie_id}",
        )
        await client.rooms.add(room)

        self = cls(client, channel, room, chat)
        self.tasks.create_task(self.start())
        return self

    async def start(self):
        while True:
            socket = await self.create_socket()
            self.room.online = True
            await self.client.rooms.update(self.room)
            await self.listen(socket)
            self.room.online = False
            await self.client.rooms.update(self.room)

    async def create_socket(self):
        socket = await session.ws_connect(
            await self.chat.fetch_ws(),
            params={
                "gift": "1",
            },
        )
        return socket

    async def listen(self, socket: aiohttp.ClientWebSocketResponse):
        while True:
            message = await socket.receive()
            if message.type == web.WSMsgType.CLOSED:
                break
            if message.type == web.WSMsgType.ERROR:
                break
            if message.type == web.WSMsgType.CLOSE:
                break
            data = message.json()
            for event in self.validate_event(data):
                await self.process_message(event)

    async def process_message(self, event: events.Event):
        if event["type"] == "comment":
            author = await self._parse_sender(event["author"])
            created_at = self._parse_createdAt(event)
            message = Message(
                id=str(event["id"]),
                room_id=self.room.key(),
                content=TextContent.of(event["message"]),
                author_id=author.key(),
                created_at=created_at,
            )
            await self.client.messages.add(message)
        elif event["type"] == "gift":
            author = await self._parse_sender(event["sender"])
            created_at = self._parse_createdAt(event)
            gifts = [
                self._parse_item(event["item"]),
                *self._parse_items(event.get("score_items", [])),
            ]
            message = Message(
                id=str(event["id"]),
                room_id=self.room.key(),
                content=TextContent.of(event["message"]),
                author_id=author.key(),
                created_at=created_at,
                gifts=gifts,
            )
            await self.client.messages.add(message)
        else:
            raise Exception(f"Unknown event type: {event['type']}")

    def _parse_item(self, item: events.Item) -> Gift:
        return Gift(
            id=item["name"],
            name=item["name"],
            amount=1,
            image_url=item["image"],
            is_paid=False,
        )

    def _parse_items(self, items: List[events.ScoreItem]) -> List[Gift]:
        gifts = []
        for item in items:
            amount = 1
            if item["text"] and item["text"].isdigit():
                amount = int(item["text"])
            gifts.append(
                Gift(
                    id=item["title"],
                    name=item["title"],
                    amount=amount,
                    is_paid=False,
                )
            )
        return gifts

    def _parse_createdAt(self, event: events.Event) -> datetime:
        created_at = datetime.fromtimestamp(event["createdAt"] / 1000)
        return created_at

    async def _parse_sender(self, sender: events.Sender) -> Author:
        author = Author(
            id=sender["id"],
            provider_id=INFO.key(),
            name=sender["name"],
            avatar_url=sender["profileImage"],
        )
        if await self.client.authors.get(f"{INFO.id}:{sender["id"]}"):
            return author
        await self.client.authors.add(author)
        return author

    def validate_event(self, data: events.EventJson) -> List[events.Event]:
        if not isinstance(data, list):
            return []
        return data

    async def stop(self):
        self.tasks.terminate()
        self.room.online = False
        await self.client.rooms.update(self.room)
