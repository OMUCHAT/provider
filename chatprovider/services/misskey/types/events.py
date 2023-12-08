from __future__ import annotations

from typing import Any, Callable, Dict, Literal, TypedDict

from .api import Note


class EventJson[Type: str, Body](TypedDict):
    type: Type
    body: Body


class Event[Type: str, Body]:
    def __init__(self, type: Type, validate: Callable[[Body], bool] | None = None):
        self.type = type
        self.validate = validate or (lambda _: True)

    def create(self, body: Body) -> EventJson:
        if not self.validate(body):
            raise ValueError(f"Invalid event body: {body}")
        return {
            "type": self.type,
            "body": body,
        }

    def __call__(self, body: EventJson[Type, Body]) -> Body | None:
        if body["type"] != self.type:
            return None
        return self.parse(body["body"])

    def parse(self, body: Body) -> Body:
        if not self.validate(body):
            raise ValueError(f"Invalid event body: {body}")
        return body


EVENTS: Dict[str, Event] = {}


def event[Type: str, Body](
    type: Type
) -> Callable[[Callable[[Body], Body]], Event[Type, Body]]:
    def decorator(cls: Callable[[Body], Body]) -> Event[Type, Body]:
        def _validate(body: Body) -> bool:
            try:
                cls(body)
            except Exception:
                return False
            return True

        event = Event[Type, Body](type, _validate)
        EVENTS[type] = event
        return event

    return decorator


class ConnectParams(TypedDict):
    withRenotes: bool
    withReplies: bool


@event("connect")
class Connect(TypedDict):
    channel: str
    id: str
    params: ConnectParams


@event("channel")
class Channel(TypedDict):
    body: Note
    type: Literal["note"]
    id: str


def parse(event: EventJson) -> Any:
    type, body = event["type"], event["body"]
    if type not in EVENTS:
        raise ValueError(f"Unexpected event type: {type}")
    return EVENTS[type].parse(body)


def parse_as[Type: str, Body](
    data: EventJson[Type, Body], event: Event[Type, Body]
) -> Body:
    return event.parse(data["body"])
