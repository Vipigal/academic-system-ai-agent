from pydantic import SecretStr

from evals.judge.agent_file import JudgeAgent
from evals.judge.verdicts import CriterionOutcome, CriterionVerdict, ItemVerdict, JudgeRequest

JUDGE_MODEL = "claude-sonnet-5-5"
SECRET_URL = SecretStr("postgresql+asyncpg://x")
AGENT = JudgeAgent("eval-judge", "Juiz", JUDGE_MODEL, "Você é o juiz.")
REQUEST = JudgeRequest(
    id="TR-01#1", question="Tranca?", answer="Não.", reference="Não dá.", rubric=("Explica", "Nega")
)


def verdict_for(
    request: JudgeRequest, outcome: CriterionOutcome = CriterionOutcome.APPROVED
) -> ItemVerdict:
    criteria = tuple(
        CriterionVerdict(criterion=number, reasoning="Porque sim.", verdict=outcome)
        for number, _ in enumerate(request.rubric, start=1)
    )
    return ItemVerdict(id=request.id, criteria=criteria)
