from dataclasses import dataclass

from api.application.agent.events import AgentEvent


@dataclass(frozen=True, slots=True)
class TurnFailed:
    pass


type ChatEvent = AgentEvent | TurnFailed
