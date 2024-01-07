import json
import re
import time
from typing import Callable, Coroutine

import aiohttp
from loguru import logger

from omuchat import Provider

HTTP_REGEX = r"(https?://)?(www\.)?"
URL_NORMALIZE_REGEX = r"(?P<protocol>https?)?:?\/?\/?(?P<domain>[^.]+\.[^\/]+)(?P<path>[^?#]+)?(?P<query>.+)?"


def get_session(provider: Provider) -> aiohttp.ClientSession:
    user_agent = json.dumps(
        [
            "OmuChat",
            {
                "id": provider.id,
                "version": provider.version,
                "repository_url": provider.repository_url,
            },
        ]
    )
    session = aiohttp.ClientSession(headers={"User-Agent": user_agent})
    return session


def normalize_url(url: str) -> str:
    match = re.match(URL_NORMALIZE_REGEX, url)
    if match is None:
        raise ValueError(f"Invalid URL: {url}")
    return f"{match.group('protocol') or 'https'}://{match.group('domain')}{match.group('path') or ''}{match.group('query') or ''}"


def timeit[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.time()
        result = func(*args, **kwargs)
        logger.info(f"{func.__name__} took {time.time() - start} seconds")
        return result

    return wrapper


def timeit_async[**P, R](
    func: Callable[P, Coroutine[None, None, R]],
) -> Callable[P, Coroutine[None, None, R]]:
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.time()
        result = await func(*args, **kwargs)
        logger.info(f"{func.__name__} took {time.time() - start} seconds")
        return result

    return wrapper
