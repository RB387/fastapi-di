from fastapi import FastAPI
from fastapi_di._injector import DependencyInjector, injector as default_injector


def inject_app(
    app: FastAPI, *, injector: DependencyInjector = default_injector
) -> FastAPI:
    app.on_event("startup")(injector.connect)
    app.on_event("shutdown")(injector.disconnect)

    return app
