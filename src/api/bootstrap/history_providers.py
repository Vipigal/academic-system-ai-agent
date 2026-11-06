from api.domain.ports.conversation import ConversationRepository
from api.persistence.agent.repository import SqlConversationRepository
from api.persistence.core.repository_adapter import RepositoryAdapter


class HistoryProviders:
    def __init__(self, adapter: RepositoryAdapter) -> None:
        self._adapter = adapter

    def conversations(self) -> ConversationRepository:
        return SqlConversationRepository(self._adapter)
