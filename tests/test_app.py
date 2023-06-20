from fastapi import FastAPI
from starlette.testclient import TestClient

from fastapi_di import Provide
from fastapi_di.app import inject_app
from tests.conftest import Service


def test_app_injection(injector):
    app = FastAPI()

    @app.get(path="/hello-world")
    def hello_world(service: Provide[Service], some_query: str) -> dict:
        assert isinstance(service, Service)
        return {"query": some_query, "is_alive": service.is_alive()}

    client = TestClient(app)

    resp = client.get("/hello-world?some_query=my-query")
    assert resp.json() == {"query": "my-query", "is_alive": True}


def test_app_injection_clients_connect(injector):
    app = FastAPI()

    @app.get(path="/hello-world")
    def hello_world(service: Provide[Service]) -> dict:
        return {
            "service_connected": service.connected,
            "workers_connected": service.workers.connected,
            "repo_connected": service.repo.connected,
            "db_connected": service.repo.db.connected,
        }

    inject_app(app)

    with TestClient(app) as client:
        resp = client.get("/hello-world")
        assert resp.json() == {
            "db_connected": True,
            "repo_connected": True,
            "service_connected": True,
            "workers_connected": True,
        }

    resp = client.get("/hello-world")
    assert resp.json() == {
        "db_connected": False,
        "repo_connected": False,
        "service_connected": False,
        "workers_connected": False,
    }
