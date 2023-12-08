from typing import List

from ..provider import ProviderService
from .misskey import MisskeyService
from .test import TestService

SERVICES: List[type[ProviderService]] = [TestService, MisskeyService]
__all__ = ["SERVICES"]
