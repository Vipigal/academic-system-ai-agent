from pathlib import Path

from evals.dashboard.payload import DashboardPayload, RunViews
from evals.run_data import RunData
from evals.run_files import RunFiles

RESULTS_DIRECTORY = Path(__file__).parent.parent / "results"
TEMPLATE_FILE = Path(__file__).parent / "template.html"
PAGE_NAME = "index.html"
DATA_PLACEHOLDER = "__DASHBOARD_DATA__"
UNSAFE_IN_SCRIPT = {
    ord("<"): "\\u003c",
    ord(">"): "\\u003e",
    ord("&"): "\\u0026",
    0x2028: "\\u2028",
    0x2029: "\\u2029",
}


class DashboardPage:
    @staticmethod
    def payload(directory: Path) -> DashboardPayload:
        runs = [
            RunViews.of(folder.name, RunData.load(RunFiles(folder)))
            for folder in sorted(directory.iterdir())
            if RunFiles(folder).manifest.exists()
        ]
        return DashboardPayload(runs=tuple(sorted(runs, key=lambda run: run.started_at)))

    @classmethod
    def render(cls, directory: Path) -> str:
        data = cls.payload(directory).model_dump_json().translate(UNSAFE_IN_SCRIPT)
        return TEMPLATE_FILE.read_text(encoding="utf-8").replace(DATA_PLACEHOLDER, data)

    @classmethod
    def write(cls, directory: Path = RESULTS_DIRECTORY) -> Path:
        page = directory / PAGE_NAME
        page.write_text(cls.render(directory), encoding="utf-8")
        return page
