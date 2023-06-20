from typing import TypeVar, Annotated, Type, TYPE_CHECKING

from fastapi import Depends

from fastapi_di._injector import injector as default_injector, DependencyInjector

T = TypeVar("T")


class _Provider:
    def __init__(self, injector: DependencyInjector):
        self.injector = injector

    def __getitem__(self, obj: Type[T]) -> Type[T]:
        return Annotated[obj, Depends(self.injector.lazy_inject(obj))]


def create_provider(injector: DependencyInjector) -> _Provider:
    return _Provider(injector)


if TYPE_CHECKING:
    from typing import Union as Provide  # hack for mypy
else:
    Provide = create_provider(default_injector)
