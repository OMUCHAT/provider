import datetime
import time

from omuchat.client import Client
from omuchat.model import Author, Channel, Message, Provider, Room, TextContent

from ..provider import ProviderService
from ..tasks import Tasks

INFO = Provider(
    id="test",
    url="example.com",
    name="Test",
    version="0.0.1",
    repository_url="https://github.com/OMUCHAT/provider",
    image_url="https://avatars.githubusercontent.com/u/73367700?v=4",
    description="Test provider",
    regex=r"example\.com/(?P<channel>[^/]+)",
)


class TestService(ProviderService):
    def __init__(self, client: Client):
        self.client = client
        self.rooms: dict[str, TestRoomService] = {}

    @property
    def info(self) -> Provider:
        return INFO

    async def start_channel(self, channel: Channel):
        if channel.url in self.rooms:
            return
        self.rooms[channel.url] = await TestRoomService.create(channel, self.client)

    async def stop_channel(self, channel: Channel):
        if channel.url not in self.rooms:
            return
        room = self.rooms[channel.url]
        await room.stop()
        del self.rooms[channel.url]


class TestRoomService:
    def __init__(self, client: Client, channel: Channel, room: Room):
        self.client = client
        self.channel = channel
        self.room = room
        self.tasks = Tasks(client.loop)

    @classmethod
    async def create(cls, channel: Channel, client: Client):
        room = Room(
            id=f"test-{channel.url}",
            provider_id=INFO.key(),
            channel_id=channel.key(),
            name=f"Test room for {channel.url}",
            online=True,
            url=channel.url,
        )
        await client.rooms.add(room)

        self = cls(client, channel, room)
        self.tasks.create_task(self.start())
        return self

    async def start(self):
        await self.client.messages.add(
            Message(
                room_id=self.channel.id,
                id=f"test-{time.time_ns()}",
                content=TextContent.of(f"Hello, world! {self.channel.url}"),
                author=Author(
                    id="tester",
                    name="tester",
                    avatar_url="https://avatars.githubusercontent.com/u/73367700?v=4",
                ),
                created_at=datetime.datetime.now(),
            )
        )

    async def stop(self):
        self.tasks.terminate()
        await self.client.rooms.remove(self.room)
