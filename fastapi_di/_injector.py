import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import partial
from typing import (
    Any,
    Type,
    TypeVar,
    get_type_hints,
    Callable,
    Union,
)

from fastapi_di._client import ClientProtocol


def is_client(cls: Type[ClientProtocol]) -> bool:
    try:
        return issubclass(cls, ClientProtocol)
    except TypeError:
        return False


T = TypeVar("T")


def _is_class(obj: Any) -> bool:
    return isinstance(obj, type)


@dataclass
class DependencyInjector:
    logger: logging.Logger = field(
        default_factory=lambda: logging.getLogger("injector")
    )
    bindings: dict = field(default_factory=dict)
    _deps: dict[Type[T], T] = field(init=False, default_factory=dict)  # type: ignore
    _postponed: list[Type[T]] = field(init=False, default_factory=list)

    def inject(self, obj: Union[Type[T], Callable]) -> Union[T, Callable]:
        obj = self.bindings.get(obj, obj)

        if instance := self._deps.get(obj):
            return instance  # type: ignore

        if _is_class(obj):
            hints = get_type_hints(obj.__init__)
        else:
            hints = get_type_hints(obj)

        clients = {}

        for name, hint in hints.items():
            bound_obj_for_hint = self.bindings.get(hint, hint)
            if not is_client(bound_obj_for_hint):
                continue

            instance = self.inject(hint)
            clients[name] = instance

        if _is_class(obj):
            self._deps[obj] = obj(**clients)  # type: ignore
        else:
            return partial(obj, **clients)

        return self._deps[obj]

    async def connect(self):
        for postponed in self._postponed:
            self.inject(postponed)

        for cls, instance in self._deps.items():
            if is_client(cls):
                self.logger.debug(f"Connecting {cls}...")
                await instance.__connect__()

    async def disconnect(self):
        for cls, instance in reversed(list(self._deps.items())):
            if is_client(cls):
                try:
                    await instance.__disconnect__()
                except Exception:
                    self.logger.exception("Failed to disconnect")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.disconnect()

    def lazy_inject(self, cls: Type[T]) -> Callable[[], T]:
        self._postponed.append(cls)

        injected = None

        def inject():
            nonlocal injected

            if injected is not None:
                return injected

            injected = self.inject(cls)
            return injected

        return inject

    def bind(self, bindings: dict):
        self.bindings = self.bindings | bindings

    @contextmanager
    def override(self, bindings: dict):
        actual_deps = self._deps
        actual_bindings = self.bindings

        try:
            self._deps = {}
            self.bindings = self.bindings | bindings
            yield
        finally:
            self._deps = actual_deps
            self.bindings = actual_bindings


injector = DependencyInjector()
