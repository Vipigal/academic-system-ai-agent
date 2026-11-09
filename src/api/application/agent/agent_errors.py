class AgentFailedError(Exception):
    pass


class AgentTimeoutError(AgentFailedError):
    pass
