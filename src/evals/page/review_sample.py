import hashlib
from collections import defaultdict
from collections.abc import Iterable, Iterator
from itertools import chain, zip_longest

from evals.golden.parts import FrozenModel
from evals.judge.verdicts import CriterionOutcome, JudgedVerdict, JudgeRequest
from evals.run_data import RunData

SAMPLE_SEED = "conferencia-do-dono-v1"
CARDS_PER_OUTCOME = 10
REVIEWED_OUTCOMES = (CriterionOutcome.APPROVED, CriterionOutcome.REJECTED)


class ReviewCard(FrozenModel):
    id: str
    execution: str
    area: str
    criterion: str
    question: str
    answer: str
    reference: str
    reasoning: str
    judge_verdict: CriterionOutcome

    @property
    def draw(self) -> str:
        return hashlib.sha256(f"{SAMPLE_SEED}:{self.id}".encode()).hexdigest()


class ReviewCards:
    @classmethod
    def of(cls, data: RunData) -> Iterator[ReviewCard]:
        areas = {record.key: record.area for record in data.records}
        for key, verdict in data.verdicts.items():
            request = data.requests.get(key)
            if request is not None and key in areas:
                yield from cls._of_verdict(request, verdict, areas[key])

    @staticmethod
    def _of_verdict(
        request: JudgeRequest, verdict: JudgedVerdict, area: str
    ) -> Iterator[ReviewCard]:
        pairs = zip(request.rubric, verdict.criteria, strict=True)
        for position, (text, criterion) in enumerate(pairs, start=1):
            yield ReviewCard(
                id=f"{request.id}/{position}",
                execution=request.id,
                area=area,
                criterion=text,
                question=request.question,
                answer=request.answer,
                reference=request.reference,
                reasoning=criterion.reasoning,
                judge_verdict=criterion.verdict,
            )


class ReviewSample:
    @classmethod
    def of(cls, data: RunData) -> tuple[ReviewCard, ...]:
        cards = list(ReviewCards.of(data))
        chosen = chain.from_iterable(
            cls._varied(card for card in cards if card.judge_verdict is outcome)
            for outcome in REVIEWED_OUTCOMES
        )
        return tuple(sorted(chosen, key=lambda card: card.draw))

    @classmethod
    def _varied(cls, cards: Iterable[ReviewCard]) -> list[ReviewCard]:
        seen: set[str] = set()
        firsts: list[ReviewCard] = []
        others: list[ReviewCard] = []
        for card in sorted(cards, key=lambda found: found.draw):
            (others if card.execution in seen else firsts).append(card)
            seen.add(card.execution)
        return [*cls._round_robin(firsts), *others][:CARDS_PER_OUTCOME]

    @staticmethod
    def _round_robin(cards: Iterable[ReviewCard]) -> Iterator[ReviewCard]:
        by_area: defaultdict[str, list[ReviewCard]] = defaultdict(list)
        for card in cards:
            by_area[card.area].append(card)
        groups = [by_area[area] for area in sorted(by_area)]
        rounds = zip_longest(*groups)
        yield from (card for cards_of_round in rounds for card in cards_of_round if card)
