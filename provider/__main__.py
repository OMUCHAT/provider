import time

from omu import Address, ConnectionListener
from omu.extension.server import App
from omuchat import Client
from omuchat.model import Author, Message, TextContent

APP = App(
    name="chatprovider",
    group="omu",
    description="Chat provider for Omu",
    version="0.1.0",
    authors=["omu"],
    license="MIT",
    repository_url="https://github.com/OMUCHAT/provider",
)
address = Address("127.0.0.1", 26423, False)
client = Client(APP, address)


class TestHandler(ConnectionListener):
    async def on_connected(self) -> None:
        tester = Author(
            id="tester",
            name="tester",
            avatar_url="https://avatars.githubusercontent.com/u/73367700?v=4",
            roles=[],
        )

        await client.chat.messages.add(
            Message(
                room_id="test",
                id=f"test-{time.time_ns()}",
                content=TextContent.of("Hello, world!"),
                author=tester,
            )
        )


client.connection.add_listener(TestHandler())


if __name__ == "__main__":
    client.run()
