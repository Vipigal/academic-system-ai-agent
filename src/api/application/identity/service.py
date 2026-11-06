from api.application.identity.dto.login import LoginDto
from api.domain.identity.errors import StudentNotFoundError, UnauthenticatedError
from api.domain.ports.identity import PersonDirectory, TokenCodec

REFERENCE_SEPARATOR = ":"


class IdentityService:
    def __init__(self, directory: PersonDirectory, codec: TokenCodec) -> None:
        self._directory = directory
        self._codec = codec

    async def login(self, reference: str) -> LoginDto:
        brand, separator, student_id = reference.strip().partition(REFERENCE_SEPARATOR)
        if not (brand and separator and student_id):
            raise StudentNotFoundError
        person_id = await self._directory.person_of(brand, student_id)
        if person_id is None:
            raise StudentNotFoundError
        return LoginDto(access_token=self._codec.issue(person_id))

    def authenticate(self, token: str) -> str:
        person_id = self._codec.person_of(token)
        if person_id is None:
            raise UnauthenticatedError
        return person_id
