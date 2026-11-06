from collections.abc import Iterator, Mapping

from evals.execution import Execution, ToolStep
from evals.golden.items import GoldenItem
from evals.graders.verdict import GraderName, Verdict
from evals.item_context import ItemContext

PROPOSE_TOOL = "propose_protocol"
OK_STATUS = "ok"
CONFIRMATION_FIELDS = ("question", "effect")
WORD_FIELD = "word"
WORD_REQUIRED = frozenset({"ACA-010", "ACA-012", "ACA-013", "ACA-014", "FIN-031"})


class ProposalOutput:
    @staticmethod
    def field(content: object, *path: str) -> object:
        for name in path:
            content = content.get(name) if isinstance(content, Mapping) else None
        return content

    @classmethod
    def service_code(cls, output: Mapping[str, object]) -> str | None:
        code = cls.field(output, "data", "service", "code")
        return code if isinstance(code, str) else None

    @staticmethod
    def is_valid_proposal(name: str, status: str) -> bool:
        return name == PROPOSE_TOOL and status == OK_STATUS


class ConfirmationGuardrail:
    @classmethod
    def problems_of(cls, complete: Mapping[str, object]) -> tuple[str, ...]:
        block = ProposalOutput.field(complete, "client_only", "confirmation")
        if not isinstance(block, Mapping):
            return ("proposta sem o bloco de confirmação do servidor",)
        return tuple(
            f"bloco de confirmação sem {name}"
            for name in cls._required(ProposalOutput.service_code(complete))
            if not ProposalOutput.field(block, name)
        )

    @staticmethod
    def _required(code: str | None) -> tuple[str, ...]:
        if code in WORD_REQUIRED:
            return (*CONFIRMATION_FIELDS, WORD_FIELD)
        return CONFIRMATION_FIELDS


class ProposalGrader:
    @classmethod
    def grade(cls, context: ItemContext, execution: Execution) -> Verdict | None:
        item = context.item
        proposals = [
            step
            for step in execution.steps
            if ProposalOutput.is_valid_proposal(step.name, step.status)
        ]
        if not item.proposal.is_set and not proposals:
            return None
        problems = list(cls._outcome_problems(item, proposals))
        for step in proposals:
            problems.extend(step.guardrail_problems)
        return Verdict.of(GraderName.PROPOSAL, problems)

    @staticmethod
    def _outcome_problems(item: GoldenItem, proposals: list[ToolStep]) -> Iterator[str]:
        expected = item.proposal
        if not expected.is_set:
            return
        accepted = sorted(expected.accepted)
        if not proposals and not expected.allows_none:
            yield f"nenhuma proposta válida, esperado {accepted}"
        for step in proposals:
            code = ProposalOutput.service_code(step.output)
            if code not in expected.services:
                yield f"propôs {code}, aceito {accepted}"
