from collections.abc import Iterator

from evals.execution import Execution
from evals.graders.leak import LeakGrader
from evals.graders.proposal import ProposalGrader
from evals.graders.refusal import RefusalGrader
from evals.graders.trajectory import TrajectoryGrader
from evals.graders.verdict import GraderName, Verdict
from evals.item_context import ItemContext


class GraderSuite:
    @classmethod
    def grade(cls, context: ItemContext, execution: Execution) -> tuple[Verdict, ...]:
        verdicts = (
            TrajectoryGrader.grade(context, execution),
            RefusalGrader.grade(context, execution),
            ProposalGrader.grade(context, execution),
            LeakGrader.grade(context, execution),
        )
        found = tuple(verdict for verdict in verdicts if verdict is not None)
        failure = execution.failure
        if failure is None:
            return found
        return tuple(cls._failed(found, context, failure))

    @staticmethod
    def _failed(
        verdicts: tuple[Verdict, ...], context: ItemContext, failure: str
    ) -> Iterator[Verdict]:
        names = {verdict.grader for verdict in verdicts}
        if context.item.proposal.is_set:
            names.add(GraderName.PROPOSAL)
        for name in sorted(names):
            yield Verdict.of(name, [f"a execução não terminou: {failure}"])
