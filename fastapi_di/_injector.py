import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Type, TypeVar, get_type_hints, Callable, Union, get_args

LegacyUnionType = type(Union[object, None])

try:
    from types import UnionType
except ImportError:
    UnionType = LegacyUnionType

from fastapi_di._client import ClientProtocol


def is_client(cls: Type[ClientProtocol]) -> bool:
    try:
        return issubclass(cls, ClientProtocol)
    except TypeError:
        return False


T = TypeVar("T")


def _get_cls_from_optional(cls: Type[T]) -> Type[T]:
    if not isinstance(cls, (UnionType, LegacyUnionType)):
        return cls

    args = get_args(cls)
    if len(args) != 2:
        raise ValueError(
            "Dependency injector doesn't support such complex hints. "
            "Supported only 'Union[cls, None]', 'cls | None', 'Optional[cls]'"
        )

    for typo in args:
        if not issubclass(typo, type(None)):
            return typo


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
        obj = _get_cls_from_optional(obj)
        obj = self.bindings.get(obj, obj)

        if instance := self._deps.get(obj):
            return instance  # type: ignore

        if _is_class(obj):
            hints = get_type_hints(obj.__init__)
        else:
            hints = get_type_hints(obj)

        clients = {}

        for name, hint in hints.items():
            hint = _get_cls_from_optional(hint)
            hint = self.bindings.get(hint, hint)

            if not is_client(hint):
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
