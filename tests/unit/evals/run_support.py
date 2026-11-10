from collections.abc import Iterator, Sequence
from pathlib import Path

from evals.dataset.items import DatasetItem
from evals.item_context import ItemContext
from evals.pricing import Pricing
from evals.records import ExecutionRecord, RunManifest, RunVersions
from evals.run_data import RunData
from evals.run_files import RunFiles
from evals.run_log import RunLog
from evals.runner import AgentDriver, ContextualizedExecution, EvalRunner

VERSIONS = RunVersions(
    model="gpt-6-luna",
    effort="low",
    prompt_version="student_agent_v1",
    skills_hash="skills",
    tools_hash="tools",
)


def key_of(run: ContextualizedExecution) -> str:
    item_id = run.context.item.id
    return f"{item_id}#{run.epoch}"


def manifest_of(
    items: Sequence[tuple[DatasetItem, int]],
    gated_items: tuple[str, ...] | None,
    extra_planned: tuple[str, ...],
) -> RunManifest:
    keys = [key_of(run) for run in planned_of(items)]
    keys.extend(extra_planned)
    gated = [item.id for item, _ in items if item.gated]
    return RunManifest(
        versions=VERSIONS,
        planned_keys=tuple(keys),
        gated_keys=tuple(key for key in keys if key.split("#")[0] in gated),
        gated_items=tuple(gated) if gated_items is None else gated_items,
        commit="abc123",
        worktree_clean=True,
        started_at="2026-11-06T00:00:00+00:00",
    )


def write_manifest(files: RunFiles, manifest: RunManifest) -> None:
    files.directory.mkdir(parents=True, exist_ok=True)
    files.manifest.write_text(manifest.model_dump_json(), encoding="utf-8")


async def run_items(
    directory: Path,
    driver: AgentDriver,
    items: Sequence[tuple[DatasetItem, int]],
    gated_items: tuple[str, ...] | None = None,
    extra_planned: tuple[str, ...] = (),
) -> RunData:
    files = RunFiles(directory)
    write_manifest(files, manifest_of(items, gated_items, extra_planned))
    log = RunLog(files, VERSIONS, Pricing.load())
    await EvalRunner(driver, log, 2).run(list(planned_of(items)))
    return RunData.load(files)


def planned_of(items: Sequence[tuple[DatasetItem, int]]) -> Iterator[ContextualizedExecution]:
    for item, total in items:
        context = ItemContext(item=item)
        for epoch in range(1, total + 1):
            yield ContextualizedExecution(context, epoch)


def record_of(data: RunData, key: str) -> ExecutionRecord:
    return next(record for record in data.records if record.key == key)
