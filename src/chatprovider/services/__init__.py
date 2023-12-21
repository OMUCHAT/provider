from typing import List

from ..provider import ProviderService
from .misskey import MisskeyService
from .twitcasting import TwitCastingService
from .youtube import YoutubeService

SERVICES: List[type[ProviderService]] = [
    MisskeyService,
    YoutubeService,
    TwitCastingService,
]
__all__ = ["SERVICES"]
