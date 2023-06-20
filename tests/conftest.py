from dataclasses import dataclass
from typing import Protocol

import pytest

from fastapi_di import BaseClient, DependencyInjector


class Connectable(BaseClient):
    connected: bool = False

    async def __connect__(self):
        self.connected = True

    async def __disconnect__(self):
        self.connected = False


class Database(Connectable):
    ...


class AnotherDatabase(Connectable):
    ...


class Repository(Connectable):
    def __init__(self, db: Database, some_params: int = 1):
        self.db = db
        self.some_params = 1


class AsyncWorkers(Connectable):
    ...


@dataclass
class Service(Connectable):
    repo: Repository
    workers: AsyncWorkers | None

    def is_alive(self):
        return bool(self.repo and self.workers)


class NonConnectableDatabase:
    ...


@dataclass
class BrokenRepo:
    db: NonConnectableDatabase


@dataclass
class BrokenService:
    repo: BrokenRepo


class RepoInterface(Protocol):
    ...


@dataclass
class ServiceWithBindings:
    repo: RepoInterface


@pytest.fixture()
def injector() -> DependencyInjector:
    return DependencyInjector()
