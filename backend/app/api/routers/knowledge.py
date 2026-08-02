from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_rag_service, get_knowledge_service
from app.domain.api_envelope import APIResponse
from app.infrastructure.db.models import User
from app.services.rag_service import RAGSearchService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/search", response_model=APIResponse[list[dict]])
async def search_knowledge(
    q: str | None = None,
    methodology: str | None = None,
    industry: str | None = None,
    department: str | None = None,
    assignee_name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    current_user: User = Depends(get_current_user),
    service: RAGSearchService = Depends(get_rag_service),
    knowledge_service = Depends(get_knowledge_service),
) -> APIResponse[list[dict]]:
    results = []
    if q and q.strip():
        from app.domain.validation import validate_search_query
        try:
            validate_search_query(q.strip())
        except ValueError as val_err:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(val_err))

        try:
            results = await service.search(
                q.strip(),
                methodology=methodology,
                industry=industry,
                department=department,
                assignee_name=assignee_name,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception:
            results = []

    # If Qdrant returns no results or query is empty/broad, fetch records from Postgres DB
    if not results:
        db_records, _ = await knowledge_service.list_paginated(page=1, page_size=100)
        filtered = []
        q_tokens = [t.lower() for t in q.strip().split()] if (q and q.strip()) else []

        for r in db_records:
            if methodology and r.methodology != methodology:
                continue
            if department and department != "Tüm Şirket" and r.department != department:
                continue
            if assignee_name and (r.meta_data or {}).get("assignee_name") != assignee_name:
                continue
            if start_date and r.resolution_date:
                if r.resolution_date.isoformat() < start_date:
                    continue
            if end_date and r.resolution_date:
                if r.resolution_date.isoformat() > end_date:
                    continue

            match_score = 1.0
            if q_tokens:
                text_corpus = f"{r.title} {r.description} {r.root_cause} {r.lessons_learned} {' '.join(r.tags or [])}".lower()
                hits = sum(1 for tok in q_tokens if tok in text_corpus)
                if hits == 0:
                    continue
                match_score = round(hits / len(q_tokens), 2)

            filtered.append({
                "id": str(r.id),
                "score": match_score if q_tokens else 1.0,
                "title": r.title,
                "description": r.description,
                "methodology": r.methodology,
                "department": r.department,
                "industry": r.industry,
                "root_cause": r.root_cause,
                "lessons_learned": r.lessons_learned,
                "tags": r.tags or [],
                "assignee_name": (r.meta_data or {}).get("assignee_name"),
                "resolution_date": r.resolution_date.isoformat() if r.resolution_date else None,
            })

        # Sort filtered fallback results by match score descending
        filtered.sort(key=lambda x: x["score"], reverse=True)
        results = filtered

    return APIResponse.ok(results)


@router.post("/ask-corporate-brain", response_model=APIResponse[dict])
async def ask_corporate_brain(
    payload: dict,
    current_user: User = Depends(get_current_user),
    knowledge_service = Depends(get_knowledge_service),
) -> APIResponse[dict]:
    query = payload.get("query", "")
    department = payload.get("department")
    if not query or not query.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Soru metni boş olamaz.")
        
    res = await knowledge_service.ask_corporate_brain(query.strip(), department=department)
    return APIResponse.ok(res)

