from typing import TypeVar, Annotated, Type

from fastapi import Depends

from fastapi_di._injector import injector as default_injector, DependencyInjector

T = TypeVar("T")


def create_provider(injector: DependencyInjector):
    def _provide(obj: Type[T]) -> Type[T]:
        return Annotated[obj, Depends(injector.lazy_inject(obj))]

    return _provide


Provide = create_provider(default_injector)
