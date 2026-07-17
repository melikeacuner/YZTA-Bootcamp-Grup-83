from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_rag_service
from app.domain.api_envelope import APIResponse
from app.infrastructure.db.models import User
from app.services.rag_service import RAGSearchService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/search", response_model=APIResponse[list[dict]])
async def search_knowledge(
    q: str,
    methodology: str | None = None,
    industry: str | None = None,
    department: str | None = None,
    current_user: User = Depends(get_current_user),
    service: RAGSearchService = Depends(get_rag_service),
) -> APIResponse[list[dict]]:
    results = await service.search(q, methodology=methodology, industry=industry, department=department)
    return APIResponse.ok(results)
