from enum import StrEnum

from api.bootstrap.settings import Settings
from evals.judge.agent_file import JudgeAgent
from evals.judge.claude_code import ClaudeCodeJudge
from evals.judge.port import Judge
from evals.judge.reserve import ChatModelCompletion, ReserveJudge


class JudgeBackend(StrEnum):
    CLAUDE = "claude"
    RESERVE = "reserve"


class JudgeBackends:
    @staticmethod
    def of(backend: JudgeBackend) -> Judge:
        agent = JudgeAgent.load()
        if backend is JudgeBackend.CLAUDE:
            return ClaudeCodeJudge(agent)
        settings = ChatModelCompletion.settings_of(Settings.from_environment())
        return ReserveJudge(agent, ChatModelCompletion(settings))
