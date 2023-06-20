from typing import Protocol, runtime_checkable


@runtime_checkable
class ClientProtocol(Protocol):
    async def __connect__(self):
        ...

    async def __disconnect__(self):
        ...
