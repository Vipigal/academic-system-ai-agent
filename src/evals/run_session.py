from evals.context_loader import ItemContextLoader
from evals.golden.loader import GoldenLoader
from evals.pricing import Pricing
from evals.records import ExecutionRecord
from evals.report.markdown import RunReport
from evals.run_data import RunData
from evals.run_files import JsonLines, RunFiles
from evals.run_log import RunLog
from evals.run_manifest import RunManifests
from evals.runner import EvalRunner
from evals.selection import PlannedExecution, RunPlan, RunRequest
from evals.student_driver import StudentDriver


class RunSession:
    def __init__(self, driver: StudentDriver, request: RunRequest) -> None:
        self._driver = driver
        self._request = request
        self._files = RunFiles(request.output)

    async def run(self) -> RunData:
        golden = GoldenLoader.load()
        planned = RunPlan.of(self._request.selection.pick(golden), self._request.repetitions)
        round_plan = RunManifests.planned_round(
            self._driver.versions, planned, golden.items, self._driver.trace_url_prefix()
        )
        await RunManifests.open(self._files, round_plan)
        contexts = await ItemContextLoader.contextualized(self._pending(planned))
        await self._runner().run(contexts)
        return RunReport.write(self._files)

    def _pending(self, planned: tuple[PlannedExecution, ...]) -> list[PlannedExecution]:
        lines = JsonLines.read(self._files.executions, ExecutionRecord)
        finished = {line.key for line in lines if line.error is None}
        return [execution for execution in planned if execution.key not in finished]

    def _runner(self) -> EvalRunner:
        log = RunLog(self._files, self._driver.versions, Pricing.load())
        concurrency = self._request.concurrency or self._driver.max_concurrency
        return EvalRunner(self._driver, log, concurrency)
