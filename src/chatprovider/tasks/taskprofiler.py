import asyncio
import time
import traceback
import typing
from typing import Callable, Dict

from loguru import logger


class Tasks:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.tasks: Dict[str, asyncio.Task] = {}
        self.times_start: Dict[str, float] = {}
        self.times: Dict[str, float] = {}
        self.times_max: Dict[str, float] = {}
        self.listeners: list[TasksListener] = []

    def terminate(self):
        for task in self.tasks.values():
            task.cancel()
            for listener in self.listeners:
                self.loop.create_task(listener.on_task_cancel(task.get_name()))

    def cancel(self, name: str | Callable):
        if callable(name):
            name = name.__name__
        if name in self.tasks:
            task = self.tasks[name]
            task.cancel()
            del task
            for listener in self.listeners:
                self.loop.create_task(listener.on_task_cancel(name))

    def create_task(self, coro: typing.Coroutine):
        name = coro.__name__

        if name in self.tasks:
            logger.warning(f"Task {name} already exists, cancelling")
            self.cancel(name)

        async def wrapper():
            self.times_start[name] = time.time()
            logger.info(f"Starting task {name}")
            try:
                for listener in self.listeners:
                    self.loop.create_task(listener.on_task_start(name))
                await coro
                for listener in self.listeners:
                    self.loop.create_task(listener.on_task_success(name))
            except Exception as e:
                for listener in self.listeners:
                    self.loop.create_task(listener.on_task_fail(name))
                traceback.print_exc()
                raise Exception(f"Task {name} failed") from e
            finally:
                logger.info(f"Finished task {name}")
                self.times[name] = time.time() - self.times_start[name]
                self.times_max[name] = max(
                    self.times_max.get(name, 0), self.times[name]
                )
                del self.times_start[name]
                del self.tasks[name]
                for listener in self.listeners:
                    self.loop.create_task(listener.on_task_finish(name))

        self.tasks[name] = asyncio.create_task(wrapper())


class TasksListener:
    async def on_task_start(self, name: str):
        ...

    async def on_task_finish(self, name: str):
        ...

    async def on_task_success(self, name: str):
        ...

    async def on_task_fail(self, name: str):
        ...

    async def on_task_cancel(self, name: str):
        ...
