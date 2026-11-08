import sys
from collections.abc import Sequence

from evals.execution import Execution
from evals.graders.verdict import Verdict
from evals.item_context import ItemContext
from evals.judge.verdicts import JudgeRequest, ToolEvidence
from evals.pricing import Pricing
from evals.records import ExecutionRecords, RunVersions
from evals.run_files import JsonLines, RunFiles

TOOLS_WITHOUT_DATA = frozenset({"load_skill"})


class RunLog:
    def __init__(self, files: RunFiles, versions: RunVersions, pricing: Pricing) -> None:
        self._files = files
        self._versions = versions
        self._pricing = pricing

    def record(
        self, context: ItemContext, execution: Execution, verdicts: Sequence[Verdict]
    ) -> None:
        cost = self._pricing.cost_of(self._versions.model, execution.usage)
        priced = (self._versions, cost)
        line = ExecutionRecords.of(context.item, execution, verdicts, priced)
        JsonLines.append(self._files.executions, line)
        if execution.failure is None:
            JsonLines.append(self._files.judge_requests, self._request_of(context, execution))
        outcome = "ok" if line.passed else "falhou"
        sys.stdout.write(f"{line.key} {outcome}\n")

    @staticmethod
    def _request_of(context: ItemContext, execution: Execution) -> JudgeRequest:
        item = context.item
        return JudgeRequest(
            id=execution.key,
            question=context.question,
            answer=execution.answer,
            reference=item.reference,
            rubric=item.rubric,
            history=item.history,
            tools=tuple(
                ToolEvidence(
                    name=step.name,
                    arguments=dict(step.arguments),
                    status=step.status,
                    output=dict(step.output),
                )
                for step in execution.steps
                if step.name not in TOOLS_WITHOUT_DATA
            ),
        )
