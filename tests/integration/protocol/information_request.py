from api.bootstrap.student_providers import StudentProviders
from api.domain.protocol.action import ProtocolAction
from api.domain.protocol.action_catalog import ServiceActions

INFORMATION = ProtocolAction.INFORMACOES_GERAIS
REQUEST_TEXT = ServiceActions.of_action(INFORMATION).request_text


async def information_token(students: StudentProviders, person_id: str, enrollment: str) -> str:
    services = await students.services_of(person_id)
    result = await services.protocol().propose_protocol(INFORMATION, enrollment, None)
    token = (result.client_only or {}).get("token")
    assert isinstance(token, str)
    return token
