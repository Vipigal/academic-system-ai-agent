from collections.abc import Callable
from dataclasses import replace

import pytest
from pydantic import BaseModel

from api.application.agent.tools.registry import (
    MAX_DESCRIPTION_LENGTH,
    ToolContractError,
    ToolRegistry,
)
from api.application.shared.page import FIRST_PAGE, PageRequest
from api.application.shared.tool_result import ToolResult
from api.domain.ontology.finance_charges import DIVIDA, MULTA_E_JUROS


def described[F: Callable[..., object]](description: str | None) -> Callable[[F], F]:
    def describe(function: F) -> F:
        function.__doc__ = description
        return function

    return describe


def stub_result() -> ToolResult[str]:
    return ToolResult.ok("x")


class HealthyTools:
    @described("Lista as dívidas do aluno. Use quando ele perguntar quanto deve.")
    @ToolRegistry.declares(DIVIDA, MULTA_E_JUROS)
    async def list_debts(self, offset: int = 0) -> ToolResult[list[int]]:
        return ToolResult.ok([offset])

    def _helper(self) -> None:
        return None


class OtherHealthyTools:
    @described("Resume a situação do aluno.")
    @ToolRegistry.declares(DIVIDA)
    async def get_summary(self) -> ToolResult[str]:
        return ToolResult.ok("summary")


class ToolsWithoutDescription:
    @described(None)
    @ToolRegistry.declares(DIVIDA)
    async def undescribed(self) -> ToolResult[str]:
        return ToolResult.ok("x")


class ToolsWithLongDescription:
    @described("x" * (MAX_DESCRIPTION_LENGTH + 1))
    @ToolRegistry.declares(DIVIDA)
    async def wordy(self) -> ToolResult[str]:
        return ToolResult.ok("x")


class ToolsWithMaximumDescription:
    @described("x" * MAX_DESCRIPTION_LENGTH)
    @ToolRegistry.declares(DIVIDA)
    async def concise(self) -> ToolResult[str]:
        return ToolResult.ok("x")


class ToolsWithoutDeclaration:
    @described("Esqueceu a ontologia.")
    async def undeclared(self) -> ToolResult[str]:
        return ToolResult.ok("x")


class ToolsWithEmptyDeclaration:
    @described("Declarou sem ontologia.")
    @ToolRegistry.declares()
    async def declared_empty(self) -> ToolResult[str]:
        return ToolResult.ok("x")


class ToolsWithUnknownOntology:
    @described("Ontologia fora do catálogo.")
    @ToolRegistry.declares(replace(DIVIDA, key="inventada"))
    async def invented(self) -> ToolResult[str]:
        return ToolResult.ok("x")


class ToolsAskingForPerson:
    @described("Recebe identidade.")
    @ToolRegistry.declares(DIVIDA)
    async def by_person(self, person_id: str) -> ToolResult[str]:
        return ToolResult.ok(person_id)


class ToolsAskingForCpf:
    @described("Recebe identidade em outra grafia.")
    @ToolRegistry.declares(DIVIDA)
    async def by_cpf(self, student_cpf: str) -> ToolResult[str]:
        return ToolResult.ok(student_cpf)


class ToolsAskingForStudentId:
    @described("Recebe identidade.")
    @ToolRegistry.declares(DIVIDA)
    async def by_stu_id(self, stu_id: str) -> ToolResult[str]:
        return ToolResult.ok(stu_id)


class ToolsAskingForContract:
    @described("Recebe contrato.")
    @ToolRegistry.declares(DIVIDA)
    async def by_contract(self, contract: str) -> ToolResult[str]:
        return ToolResult.ok(contract)


class ToolsAskingForRa:
    @described("Recebe RA.")
    @ToolRegistry.declares(DIVIDA)
    async def by_ra(self, ra: str) -> ToolResult[str]:
        return ToolResult.ok(ra)


class ToolsAskingForAluno:
    @described("Recebe aluno.")
    @ToolRegistry.declares(DIVIDA)
    async def by_aluno(self, aluno: str) -> ToolResult[str]:
        return ToolResult.ok(aluno)


class SyncTools:
    @described("Tool síncrona.")
    @ToolRegistry.declares(DIVIDA)
    def blocking(self) -> ToolResult[str]:
        return stub_result()


class ToolsReturningInt:
    @described("Devolve int.")
    @ToolRegistry.declares(DIVIDA)
    async def counting(self) -> int:
        return 1


class ToolsWithPublicClassmethod:
    @described("Tool normal.")
    @ToolRegistry.declares(DIVIDA)
    async def regular(self) -> ToolResult[str]:
        return stub_result()

    @classmethod
    def build(cls) -> None:
        return None


class ToolsWithPublicStaticmethod:
    @described("Tool normal.")
    @ToolRegistry.declares(DIVIDA)
    async def regular(self) -> ToolResult[str]:
        return stub_result()

    @staticmethod
    def helper() -> None:
        return None


class ToolsWithPagination:
    @described("Lista paginada.")
    @ToolRegistry.declares(DIVIDA)
    async def paged(self, page: PageRequest = FIRST_PAGE) -> ToolResult[str]:
        return ToolResult.ok(str(page))


class IdentityFilter(BaseModel):
    term: str
    tax_id: str


class ToolsAskingThroughFilter:
    @described("Recebe identidade dentro de um filtro.")
    @ToolRegistry.declares(DIVIDA)
    async def by_filter(self, query: IdentityFilter | None = None) -> ToolResult[str]:
        return ToolResult.ok(str(query))


class NavigationFilter(BaseModel):
    term: str
    subject: str


class ToolsWithNavigationFilter:
    @described("Filtro só navega.")
    @ToolRegistry.declares(DIVIDA)
    async def by_navigation(self, query: NavigationFilter) -> ToolResult[str]:
        return ToolResult.ok(query.term)


def test_describe_reads_name_description_and_ontologies_from_the_class() -> None:
    definitions = ToolRegistry.describe(HealthyTools)

    assert [definition.name for definition in definitions] == ["list_debts"]
    assert definitions[0].description == (
        "Lista as dívidas do aluno. Use quando ele perguntar quanto deve."
    )
    assert definitions[0].ontologies == (DIVIDA, MULTA_E_JUROS)


def test_group_without_tools_describes_nothing() -> None:
    assert ToolRegistry.describe(object) == ()


async def test_registry_binds_each_tool_to_its_group_instance() -> None:
    registry = ToolRegistry(HealthyTools(), OtherHealthyTools())

    by_name = {tool.definition.name: tool for tool in registry.tools}

    assert set(by_name) == {"list_debts", "get_summary"}
    assert await by_name["list_debts"].handler(offset=3) == ToolResult.ok([3])


def test_registry_refuses_the_same_tool_name_twice() -> None:
    with pytest.raises(ToolContractError, match="list_debts"):
        ToolRegistry(HealthyTools(), HealthyTools())


def test_description_at_the_limit_is_accepted() -> None:
    assert ToolRegistry.describe(ToolsWithMaximumDescription)


@pytest.mark.parametrize(
    ("group", "reason"),
    [
        (ToolsWithoutDescription, "undescribed"),
        (ToolsWithLongDescription, "wordy"),
        (ToolsWithoutDeclaration, "undeclared"),
        (ToolsWithEmptyDeclaration, "declared_empty"),
        (ToolsWithUnknownOntology, "inventada"),
        (ToolsAskingForPerson, "person_id"),
        (ToolsAskingForCpf, "student_cpf"),
        (ToolsAskingThroughFilter, "tax_id"),
        (ToolsAskingForStudentId, "stu_id"),
        (ToolsAskingForContract, "contract"),
        (ToolsAskingForRa, "ra"),
        (ToolsAskingForAluno, "aluno"),
        (SyncTools, "async"),
        (ToolsReturningInt, "ToolResult"),
        (ToolsWithPublicClassmethod, "build"),
        (ToolsWithPublicStaticmethod, "helper"),
    ],
)
def test_contract_violation_names_what_is_wrong(group: type, reason: str) -> None:
    with pytest.raises(ToolContractError, match=reason):
        ToolRegistry.describe(group)


def test_filter_that_only_navigates_is_accepted() -> None:
    assert ToolRegistry.describe(ToolsWithNavigationFilter)


def test_paginated_tool_with_page_request_is_accepted() -> None:
    assert ToolRegistry.describe(ToolsWithPagination)
