import re

HTTP_REGEX = r"(https?://)?(www\.)?"
URL_NORMALIZE_REGEX = r"(?P<protocol>https?)?:?\/?\/?(?P<domain>[^.]+\.[^\/]+)(?P<path>[^?#]+)?(?P<query>.+)?"


def normalize_url(url: str) -> str:
    match = re.match(URL_NORMALIZE_REGEX, url)
    if match is None:
        raise ValueError(f"Invalid URL: {url}")
    return f"{match.group('protocol') or 'https'}://{match.group('domain')}{match.group('path') or ''}{match.group('query') or ''}"
