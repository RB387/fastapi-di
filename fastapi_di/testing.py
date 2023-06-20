from unittest.mock import AsyncMock

from fastapi_di import ClientProtocol


__all__ = ("get_client_mock_cls", "ClientMock")


def get_client_mock_cls(return_value):
    class ClientMetaclassMock(ClientProtocol):
        __annotations__ = {}

        def __new__(cls, *args, **kwargs):
            return return_value

    return ClientMetaclassMock


class ClientMock(AsyncMock):
    @property
    def mock_cls(self):
        return get_client_mock_cls(self)

    async def __connect__(self):
        ...

    async def __disconnect(self):
        ...

    def __call__(self, *args, **kwargs):
        return self.__class__(*args, **kwargs)
