from collections.abc import Mapping

from api.domain.protocol.academic_actions import ACADEMIC_ACTIONS
from api.domain.protocol.action import ProtocolAction, ServiceAction
from api.domain.protocol.document_actions import DOCUMENT_ACTIONS
from api.domain.protocol.support_actions import SUPPORT_ACTIONS

SERVICE_ACTIONS = (*ACADEMIC_ACTIONS, *DOCUMENT_ACTIONS, *SUPPORT_ACTIONS)
BY_CODE = {item.code: item for item in SERVICE_ACTIONS}
BY_ACTION = {item.action: item for item in SERVICE_ACTIONS if item.action is not None}


class ServiceActions:
    @staticmethod
    def find(code: str) -> ServiceAction | None:
        return BY_CODE.get(code)

    @staticmethod
    def proposable(code: str) -> ServiceAction | None:
        entry = BY_CODE.get(code)
        if entry is None or entry.action is None:
            return None
        return entry

    @staticmethod
    def of_action(action: ProtocolAction) -> ServiceAction:
        return BY_ACTION[action]

    @staticmethod
    def titles() -> Mapping[str, str]:
        return {code: item.title for code, item in BY_CODE.items()}
