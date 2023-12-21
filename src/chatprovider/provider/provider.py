import abc

from omuchat import Client
from omuchat.model import Channel, Provider


class ProviderService(abc.ABC):
    @abc.abstractmethod
    def __init__(self, client: Client):
        ...

    @property
    @abc.abstractmethod
    def info(self) -> Provider:
        ...

    @abc.abstractmethod
    async def start_channel(self, channel: Channel):
        ...

    @abc.abstractmethod
    async def stop_channel(self, channel: Channel):
        ...
