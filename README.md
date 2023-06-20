# FastAPI Magic DI
Dependency Injector for FastAPI that makes your life easier


What are the problems with FastAPI’s dependency injector? 
1) It forces you to use global variables. 
2) It is hard to test. For example, what if you need to mock only one embedded dependency?  
3) It makes your project highly dependent on FastAPI’s injector by using “Depends” everywhere.

To solve these problems, you can use this dead-simple Dependency Injector that will make development so much easier.

* [Install](#install)
* [Getting Started](#getting-started)
* [Clients Configuration](#clients-configuration)
  * [Zero config clients](#zero-config-clients)
  * [Clients with Config](#clients-with-config)
* [Using interfaces instead of implementations](#using-interfaces-instead-of-implementations)
* [Testing](#testing)


## Install
```bash
pip install fastapi-magic-di
```

## Getting Started

```python
from fastapi import FastAPI
from fastapi_di import Provide, ClientProtocol
from fastapi_di.app import inject_app

app = inject_app(FastAPI())


class Database:
    connected: bool = False
    
    def __connect__(self):
        self.connected = True
    
    def __disconnect__(self):
        self.connected = False
        
        

class Service(ClientProtocol):
    def __init__(self, db: Database):
        self.db = db
        
    def is_connected(self):
        return self.db.connected
    

@app.get(path="/hello-world")
def hello_world(service: Provide(Service)) -> dict:
    return {
        "is_connected": service.is_connected()
    }

```

That's all!
his simple code will recursively inject all dependencies and connect them using the `__connect__` and `__disconnect__` magic methods.

But what happened there?
1) We created a new FastAPI app and injected it. The `inject_app` function makes the injector connect all clients on app startup and disconnect them on shutdown. That’s how you can open and close all connections (e.g., session to DB).
2) We defined new classes with `__connect__` and `__disconnect__` magic methods. __That’s how the injector finds classes that need to be injected__. The injector uses duck typing to check if some class has these methods. It means you don’t need to inherit from `ClientProtocol` (but you can to reduce the number of code lines).
3) Wrapped the `Service` type hint into `Provide` so that FastAPI can use our DI. __Please note__: you need to use `Provide` only in FastAPI endpoints, which makes your codebase independent from FastAPI and this Dependency Injector.
4) PROFIT!

As you can see, in this example, you don’t need to write special constructors to store your dependencies in global variables. All you need to do to complete the startup logic is to write it in the `__connect__` method.


## Clients Configuration
This dependency injector promotes the idea of ‘zero-config clients’, but you can still use configurations if you prefer

### Zero config clients
Simply fetch everything needed from the environment. There is no need for an additional configuration file. In this case, the library includes the env_fields module to simplify zero-client development

```python
from dataclasses import dataclass, field

from fastapi_di.env_fields import field_str, field_bool

from redis.asyncio import Redis as RedisClient, from_url


@dataclass
class Redis:
    url: str = field_str("REDIS_URL")
    decode_responses: bool = field_bool("REDIS_DECODE_RESPONSES")
    client: RedisClient = field(init=False)

    async def __connect__(self):
        self.client = await from_url(self.url, decode_responses=self.decode_responses)
        await self.client.ping()

    async def __disconnect__(self):
        await self.client.close()

    @property
    def db(self) -> RedisClient:
        return self.client
```

Just use the `field_*` functions in dataclasses to fetch variables from the environment and cast them to the required data type.


### Clients with Config
Inject config as dependency :)

```python
from dataclasses import dataclass, field

from fastapi_di import ClientProtocol

from redis.asyncio import Redis as RedisClient


@dataclass
class RedisConfig(ClientProtocol):
    url: str = "SOME_URL"
    decode_responses: bool = True


class Redis:
    db: RedisClient
    
    def __init__(self, config: RedisConfig):
        self.db = RedisClient(config.url, decode_responses=config.decode_responses)

    async def __connect__(self):
        await self.db.ping()

    async def __disconnect__(self):
        await self.db.close()
```


## Using interfaces instead of implementations
Sometimes, you may not want to stick to a certain interface implementation everywhere. Therefore, you can use interfaces (protocols, abstract classes) with Dependency Injection (DI). With DI, you can effortlessly bind an implementation to an interface and subsequently update it if necessary.

```python
from typing import Protocol

from fastapi import FastAPI
from fastapi_di import Provide, ClientProtocol, injector
from fastapi_di.app import inject_app


class MyInterface(Protocol):
    def do_something(self) -> bool:
        ...


class MyInterfaceImplementation(ClientProtocol):
    def do_something(self) -> bool:
        return True
    

app = inject_app(FastAPI())

injector.bind({MyInterface: MyInterfaceImplementation})



@app.get(path="/hello-world")
def hello_world(service: Provide(MyInterface)) -> dict:
    return {
        "result": service.do_something(),
    }
```

Using `injector.bind`, you can bind implementations that will be injected everywhere the bound interface is used. 


## Testing
If you need to mock a dependency in tests, you can easily do so by using the `injector.override` context manager and still use this dependency injector.

To mock clients, you can use `ClientMock` from the `testing` module.

```python
from fastapi_di import injector
from fastapi_di.testing import ClientMock


def test_http_handler(client):
    service_mock = ClientMock()
    
    with injector.override({Service: service_mock.mock_cls}):
        resp = client.post('/hello-world')
        
    assert resp.status_code == 200
```