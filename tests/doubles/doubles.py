from collections.abc import Callable, Mapping
from typing import Any

from dishka import AsyncContainer, Provider, Scope, make_async_container

from api.bootstrap.containers import Containers
from api.bootstrap.session_providers import GivenSession, HttpSession
from api.bootstrap.settings import Settings

type Objects = Mapping[Any, object]


class Doubles(Provider):
    def __init__(self, objects: Objects) -> None:
        super().__init__(scope=Scope.APP)
        for kind, double in objects.items():
            self.provide(Doubles._constant(double), provides=kind, override=True)

    @staticmethod
    def _constant(double: object) -> Callable[[], object]:
        return lambda: double


class DoubleContainers:
    @staticmethod
    def http(settings: Settings, objects: Objects) -> AsyncContainer:
        return make_async_container(
            *Containers.graph(), HttpSession(), Doubles(objects), context={Settings: settings}
        )

    @staticmethod
    def students(settings: Settings, objects: Objects) -> AsyncContainer:
        return make_async_container(
            *Containers.graph(), GivenSession(), Doubles(objects), context={Settings: settings}
        )
