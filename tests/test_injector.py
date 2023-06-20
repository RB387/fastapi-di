import pytest

from tests.conftest import (
    Service,
    Repository,
    Database,
    AsyncWorkers,
    BrokenService,
    RepoInterface,
    ServiceWithBindings,
    AnotherDatabase,
)


@pytest.mark.asyncio
async def test_class_injection_success(injector):
    injected_service = injector.inject(Service)
    assert injected_service.is_alive()

    assert isinstance(injected_service.repo, Repository)
    assert isinstance(injected_service.repo.db, Database)
    assert isinstance(injected_service.workers, AsyncWorkers)

    assert not injected_service.repo.connected
    assert not injected_service.repo.db.connected
    assert not injected_service.workers.connected

    await injector.connect()

    assert injected_service.repo.connected
    assert injected_service.repo.db.connected
    assert injected_service.workers.connected

    await injector.disconnect()

    assert not injected_service.repo.connected
    assert not injected_service.repo.db.connected
    assert not injected_service.workers.connected


def test_function_injection_success(injector):
    def run_service(service: Service):
        return service

    injected = injector.inject(run_service)

    service = injected()

    assert service.is_alive()
    assert isinstance(service, Service)


def test_class_injection_missing_class(injector):
    with pytest.raises(TypeError):
        injector.inject(BrokenService)


@pytest.mark.asyncio
async def test_class_injection_with_bindings(injector):
    injector.bind({RepoInterface: Repository})

    injected_service = injector.inject(ServiceWithBindings)

    assert isinstance(injected_service.repo, Repository)
    assert isinstance(injected_service.repo.db, Database)

    await injector.connect()

    assert injected_service.repo.connected
    assert injected_service.repo.db.connected

    await injector.disconnect()

    assert not injected_service.repo.connected
    assert not injected_service.repo.db.connected


def test_lazy_inject(injector):
    get_injected_cls = injector.lazy_inject(Service)
    injected_service = get_injected_cls()

    assert isinstance(injected_service, Service)
    assert injected_service is get_injected_cls()


def test_overriden_injection(injector):
    service = injector.inject(Service)

    with injector.override({Database: AnotherDatabase}):
        service_with_overriden_deps = injector.inject(Service)

        assert isinstance(service_with_overriden_deps, Service)
        assert isinstance(service_with_overriden_deps.repo.db, AnotherDatabase)
        assert isinstance(service.repo.db, Database)
        assert service is not service_with_overriden_deps

    service_after_overriden_injection = injector.inject(Service)
    assert isinstance(service_after_overriden_injection.repo.db, Database)
    assert service is service_after_overriden_injection
