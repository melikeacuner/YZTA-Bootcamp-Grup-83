import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.infrastructure.repositories.qdrant_repository import QdrantUnavailableError
from app.services.auth_service import EmailAlreadyRegisteredError, InvalidCredentialsError
from app.services.knowledge_service import RecordNotFoundError
from app.services.rag_service import DegradedModeError
from app.services.session_service import (
    AllStepsAnsweredError,
    FollowUpLimitExceededError,
    SessionIncompleteError,
    SessionNotActiveError,
)

logger = logging.getLogger(__name__)


def _error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"status": "error", "data": None, "error": message})


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(EmailAlreadyRegisteredError)
    async def _email_taken(request: Request, exc: EmailAlreadyRegisteredError) -> JSONResponse:
        return _error_response(409, "Bu e-posta adresi zaten kayitli")

    @app.exception_handler(InvalidCredentialsError)
    async def _invalid_credentials(request: Request, exc: InvalidCredentialsError) -> JSONResponse:
        return _error_response(401, "Gecersiz e-posta veya sifre")

    @app.exception_handler(RecordNotFoundError)
    async def _record_not_found(request: Request, exc: RecordNotFoundError) -> JSONResponse:
        return _error_response(404, "Kayit bulunamadi")

    @app.exception_handler(SessionNotActiveError)
    async def _session_not_active(request: Request, exc: SessionNotActiveError) -> JSONResponse:
        return _error_response(409, "Oturum artik aktif degil")

    @app.exception_handler(SessionIncompleteError)
    async def _session_incomplete(request: Request, exc: SessionIncompleteError) -> JSONResponse:
        return _error_response(400, "Oturum tum zorunlu adimlar tamamlanmadan kapatilamaz")

    @app.exception_handler(FollowUpLimitExceededError)
    async def _follow_up_limit(request: Request, exc: FollowUpLimitExceededError) -> JSONResponse:
        return _error_response(400, "Bu adim icin takip sorusu limitine ulasildi")

    @app.exception_handler(AllStepsAnsweredError)
    async def _all_steps_answered(request: Request, exc: AllStepsAnsweredError) -> JSONResponse:
        return _error_response(400, "Tum adimlar zaten yanitlandi")

    @app.exception_handler(DegradedModeError)
    async def _degraded_mode(request: Request, exc: DegradedModeError) -> JSONResponse:
        return _error_response(503, "Semantik arama/vektor deposu gecici olarak kullanilamiyor")

    @app.exception_handler(QdrantUnavailableError)
    async def _qdrant_unavailable(request: Request, exc: QdrantUnavailableError) -> JSONResponse:
        return _error_response(503, "Vektor deposu gecici olarak kullanilamiyor")

    @app.exception_handler(ValueError)
    async def _value_error(request: Request, exc: ValueError) -> JSONResponse:
        return _error_response(422, str(exc))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Beklenmeyen hata", exc_info=exc)
        return _error_response(500, "Beklenmeyen bir hata olustu")
