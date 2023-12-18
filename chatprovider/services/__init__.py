from typing import List

from chatprovider.services.youtube.youtube import YoutubeService

from ..provider import ProviderService
from .misskey import MisskeyService

SERVICES: List[type[ProviderService]] = [MisskeyService, YoutubeService]
__all__ = ["SERVICES"]
