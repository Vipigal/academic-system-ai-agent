from evals.execution import Execution
from evals.graders.verdict import GraderName, Verdict
from evals.item_context import ItemContext


class TrajectoryGrader:
    @staticmethod
    def grade(context: ItemContext, execution: Execution) -> Verdict:
        tools = context.item.tools
        missing = sorted(set(tools.expected) - execution.tools_used)
        forbidden = sorted(set(tools.forbidden) & execution.tools_called)
        problems = [f"faltou a tool {tool}" for tool in missing]
        problems.extend(f"chamou a tool proibida {tool}" for tool in forbidden)
        return Verdict.of(GraderName.TRAJECTORY, problems)
