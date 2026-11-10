from dishka import AsyncContainer, make_async_container
from langchain_core.language_models import BaseChatModel

from api.bootstrap.settings import Settings
from evals.eval_container import EvalContainer
from evals.student_driver import StudentDriver
from tests.doubles.doubles import Doubles, Objects
from tests.doubles.scripted_model import ScriptedChatModel


def evaluation_container(doubles: Objects, settings: Settings) -> AsyncContainer:
    return make_async_container(
        *EvalContainer.graph(),
        Doubles({BaseChatModel: ScriptedChatModel.standard(), **doubles}),
        context={Settings: settings},
    )


def standard_driver(settings: Settings) -> StudentDriver:
    container = evaluation_container({}, settings)
    return StudentDriver(container, EvalContainer.versions_of(container, settings))
