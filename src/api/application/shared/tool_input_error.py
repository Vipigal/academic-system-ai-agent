class ToolInputError(Exception):
    def __init__(self, explanation: str) -> None:
        super().__init__(explanation)
        self.explanation = explanation
