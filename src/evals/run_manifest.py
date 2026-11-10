import asyncio
import time
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime

from evals.dataset.items import DatasetItem
from evals.records import PlannedRound, RunManifest, RunVersions
from evals.run_files import RunFiles
from evals.selection import PlannedExecution

UNKNOWN_COMMIT = "desconhecido"
GIT_COMMAND = "git"


class RunConflictError(RuntimeError):
    pass


class RunManifests:
    @staticmethod
    def planned_round(
        versions: RunVersions,
        planned: Sequence[PlannedExecution],
        items: Iterable[DatasetItem],
        trace_url_prefix: str | None,
    ) -> PlannedRound:
        return PlannedRound(
            versions=versions,
            planned_keys=tuple(run.key for run in planned),
            gated_keys=tuple(run.key for run in planned if run.item.gated),
            gated_items=tuple(item.id for item in items if item.gated),
            trace_url_prefix=trace_url_prefix,
        )

    @classmethod
    async def open(cls, files: RunFiles, planned: PlannedRound) -> None:
        files.directory.mkdir(parents=True, exist_ok=True)
        if not files.manifest.exists():
            manifest = await cls._new(planned)
            files.manifest.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
            return
        existing = RunManifest.model_validate_json(files.manifest.read_text(encoding="utf-8"))
        if not existing.same_round(planned):
            raise RunConflictError(f"O diretório guarda outra rodada: {existing.versions}")

    @classmethod
    async def _new(cls, planned: PlannedRound) -> RunManifest:
        commit = await cls._git("rev-parse", "HEAD")
        status = await cls._git("status", "--porcelain")
        return RunManifest(
            **dict(planned),
            commit=commit or UNKNOWN_COMMIT,
            worktree_clean=status == "",
            started_at=datetime.fromtimestamp(time.time(), UTC).isoformat(),
        )

    @staticmethod
    async def _git(*arguments: str) -> str | None:
        process = await asyncio.create_subprocess_exec(
            GIT_COMMAND,
            *arguments,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await process.communicate()
        return stdout.decode().strip() if process.returncode == 0 else None
