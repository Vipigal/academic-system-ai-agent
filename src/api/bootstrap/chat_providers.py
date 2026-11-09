from dishka import Provider, Scope, provide, provide_all

from api.application.chat.rate_limit import ChatRateLimit
from api.application.chat.service import ChatService
from api.application.chat.turn_input import ChatOptions
from api.bootstrap.chat_agent_scope import ChatAgentScope
from api.bootstrap.session_providers import PersonId
from api.bootstrap.settings import Settings
from api.domain.ports.conversation import ConversationRepository
from api.persistence.agent.repository import SqlConversationRepository


class ChatProvider(Provider):
    scope = Scope.REQUEST

    conversations = provide(SqlConversationRepository, provides=ConversationRepository)
    chat = provide_all(ChatAgentScope, ChatRateLimit)

    @provide
    def service(
        self,
        conversations: ConversationRepository,
        agent_scope: ChatAgentScope,
        person: PersonId,
        settings: Settings,
    ) -> ChatService:
        options = ChatOptions(person, settings.history_window, settings.agent_model)
        return ChatService(conversations, agent_scope.traced_agent, options)
