from collections.abc import Mapping

PORTUGUESE_NAMES: Mapping[str, str] = {
    "ADM": "Administração",
    "ADS": "Análise e Desenvolvimento de Sistemas",
    "CON": "Ciências Contábeis",
    "PED": "Pedagogia",
    "DIR": "Direito",
    "ENF": "Enfermagem",
    "ENC": "Engenharia Civil",
    "PSI": "Psicologia",
}


class CourseNames:
    @staticmethod
    def portuguese(code: str) -> str | None:
        return PORTUGUESE_NAMES.get(code)
