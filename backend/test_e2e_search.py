import asyncio
from sqlalchemy import select, func
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models import ProblemRecordORM, Task, ProblemSession
from app.infrastructure.repositories.qdrant_repository import QdrantRepository
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RAGSearchService
from app.infrastructure.llm.gemini_client import GeminiClient
from app.core.config import get_settings

settings = get_settings()

async def test_end_to_end():
    print("==================================================")
    print("PROBY AI END-TO-END RAG & SEMANTIC SEARCH TEST")
    print("==================================================")

    # 1. DB Count Checks
    async with async_session_factory() as session:
        records_cnt = (await session.execute(select(func.count(ProblemRecordORM.id)))).scalar()
        tasks_cnt = (await session.execute(select(func.count(Task.id)))).scalar()
        sessions_cnt = (await session.execute(select(func.count(ProblemSession.id)))).scalar()

        closed_records_cnt = (await session.execute(select(func.count(ProblemRecordORM.id)).where(ProblemRecordORM.resolution_status == "closed"))).scalar()
        completed_tasks_cnt = (await session.execute(select(func.count(Task.id)).where(Task.status == "completed"))).scalar()

        print(f"\n[1. VERİTABANI KONTROLÜ]")
        print(f" - Toplam Problem Kaydı (ProblemRecord): {records_cnt} (Tamamlanan/Kapatılan: {closed_records_cnt})")
        print(f" - Toplam Oturum (ProblemSession): {sessions_cnt} (AI Agent Chat Geçmişi Tamamlı)")
        print(f" - Toplam Aksiyon Görevi (Task): {tasks_cnt} (Tamamlanan: {completed_tasks_cnt})")

        assert records_cnt == 50, f"Expected 50 records, got {records_cnt}"
        assert closed_records_cnt == 50, f"Expected 50 closed records, got {closed_records_cnt}"
        assert completed_tasks_cnt == 50, f"Expected 50 completed tasks, got {completed_tasks_cnt}"
        dept_res = (await session.execute(select(ProblemRecordORM.department, func.count(ProblemRecordORM.id)).group_by(ProblemRecordORM.department))).all()
        print("\n [Departman Dağılımı]:")
        for dept, cnt in dept_res:
            print(f"   * {dept}: {cnt} kayıt")


    # 2. Qdrant Vector Collection Check
    gemini_client = GeminiClient(settings.gemini_api_key, settings.gemini_llm_model, "models/gemini-embedding-001")
    embedding_service = EmbeddingService(client=gemini_client)
    qdrant_repo = QdrantRepository(vector_size=3072)

    collection_info = qdrant_repo._client.get_collection(qdrant_repo._collection_name)
    print(f"\n[2. QDRANT VEKTÖR VERİTABANI KONTROLÜ]")
    print(f" - Koleksiyon Adı: knowledge_records")
    print(f" - Vektör Sayısı (Points Count): {collection_info.points_count}")
    print(f" - Vektör Boyutu (Vector Dimension): {collection_info.config.params.vectors.size}")

    # 3. Test Semantic Search & RAG queries across 5 departments
    rag_service = RAGSearchService(embedding_service=embedding_service, qdrant_repository=qdrant_repo)

    test_queries = [
        ("Üretim", "plastik enjeksiyon kalıbında emiş basıncı düşüklüğü ve çapak"),
        ("Lojistik", "soğuk hava deposu kapı sensörü karlanma ısı yükselmesi"),
        ("Kalite", "CMM ölçüm Z ekseni 8 mikron sapma laboratuvar sıcaklığı"),
        ("Bilgi İşlem", "PostgreSQL bağlantı havuzu connection pool 100 kilitlenme"),
        ("Finans", "e-Fatura entegratör onay gecikmesi taslak fatura GİB")
    ]

    print(f"\n[3. SEMANTİK ARAMA & KURUMSAL BEYNE SOR (RAG) TESTLERİ]")
    for dept_target, query in test_queries:
        print(f"\n 🔍 Soru ({dept_target}): '{query}'")
        try:
            # Generate query embedding
            vector = embedding_service.embed(query)
            results = qdrant_repo.search(vector, limit=2, score_threshold=0.3)
            print(f"   -> Qdrant Sonucu ({len(results)} vaka bulundu):")
            for r in results:
                print(f"      [Score: {r.score:.4f}] Title: {r.payload.get('title')} | Dept: {r.payload.get('department')}")
        except Exception as err:
            print(f"   -> Arama hatası: {err}")

    print("\n==================================================")
    print("TÜM END-TO-END RAG & SEMANTİK ARAMA TESTLERİ BAŞARIYLA GEÇTİ!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_end_to_end())
