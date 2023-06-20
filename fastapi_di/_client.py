from typing import Protocol, runtime_checkable


@runtime_checkable
class ClientProtocol(Protocol):
    async def __connect__(self):
        ...

    async def __disconnect__(self):
        ...


class BaseClient:
    """
    You can inherit from this class to make the dependency visible for DI
    without adding these empty methods.
    """

    async def __connect__(self):
        ...

    async def __disconnect__(self):
        ...
