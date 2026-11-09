from pathlib import Path

from evals.page.payload import PagePayloads
from evals.run_data import RunData

TEMPLATE_FILE = Path(__file__).parent / "template.html"
DATA_PLACEHOLDER = "__RUN_DATA__"
LINE_SEPARATOR = 0x2028
PARAGRAPH_SEPARATOR = 0x2029
UNSAFE_IN_SCRIPT = {
    ord("<"): "\\u003c",
    ord(">"): "\\u003e",
    ord("&"): "\\u0026",
    LINE_SEPARATOR: "\\u2028",
    PARAGRAPH_SEPARATOR: "\\u2029",
}


class ResultsPage:
    @staticmethod
    def render(data: RunData) -> str:
        payload = PagePayloads.of(data).model_dump_json()
        safe = payload.translate(UNSAFE_IN_SCRIPT)
        template = TEMPLATE_FILE.read_text(encoding="utf-8")
        return template.replace(DATA_PLACEHOLDER, safe)
