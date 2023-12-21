from typing import Callable

from loguru import logger
from omuchat import App, Channel, Client, events
from omuchat.model import Message

from .provider import ProviderService
from .services import SERVICES

APP = App(
    name="builtin-provider",
    group="omu",
    description="Chat provider for Omu",
    version="0.1.0",
    authors=["omu"],
    license="MIT",
    repository_url="https://github.com/OMUCHAT/provider",
)
client = Client(APP)


def instance[T](cls: Callable[[], T]) -> T:
    return cls()


services = {}
for service_cls in SERVICES:
    service = service_cls(client)
    services[service.info.key()] = service


async def register_services():
    for service in services.values():
        await client.providers.add(service.info)


@client.on(events.ChannelCreate)
async def on_channel_create(channel: Channel):
    service = get_provider(channel)
    if service is None:
        return
    if channel.active:
        try:
            await service.start_channel(channel)
            logger.info(f"Channel {channel.url} activated")
        except Exception as e:
            logger.error(f"Failed to activate channel {channel.url}: {e}")


@client.on(events.ChannelDelete)
async def on_channel_delete(channel: Channel):
    service = get_provider(channel)
    if service is None:
        return
    if channel.active:
        await service.stop_channel(channel)
        logger.info(f"Channel {channel.url} deactivated")


@client.on(events.ChannelUpdate)
async def on_channel_update(channel: Channel):
    service = get_provider(channel)
    if service is None:
        return
    if channel.active:
        await service.start_channel(channel)
        try:
            await service.start_channel(channel)
            logger.info(f"Channel {channel.url} activated")
        except Exception as e:
            logger.error(f"Failed to activate channel {channel.url}: {e}")
    else:
        await service.stop_channel(channel)
        logger.info(f"Channel {channel.url} deactivated")


def get_provider(channel: Channel) -> ProviderService | None:
    if channel.provider_id not in services:
        return None
    return services[channel.provider_id]


async def start_channels():
    async for channel in client.channels.iter():
        service = get_provider(channel)
        if service is None:
            continue
        if channel.active:
            try:
                await service.start_channel(channel)
                logger.info(f"Channel {channel.url} activated")
            except Exception as e:
                logger.error(f"Failed to activate channel {channel.url}: {e}")
            logger.info(f"Channel {channel.url} activated")


@client.on(events.Ready)
async def on_ready():
    await register_services()
    await start_channels()
    logger.info("Ready!")


@client.on(events.MessageCreate)
async def on_message_create(message: Message):
    print(f"Message created: {message.text}")
    for gift in message.gifts:
        print(f"Gift: {gift.name} x{gift.amount}")
