import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models import ProblemSession, ProblemRecordORM, Task, User
from app.domain.enums import SessionStatus, EmbeddingStatus
from app.services.embedding_pipeline import EmbeddingPipeline
from app.services.embedding_service import EmbeddingService
from app.infrastructure.repositories.qdrant_repository import QdrantRepository
from app.core.config import get_settings
from app.infrastructure.llm.gemini_client import GeminiClient

settings = get_settings()

POOL_SCENARIOS = [
    {
        "title": "SL3-SL4 İzole Zone Arasında Nutanix AHV vLAN Microsegmentation Paket Düşmesi ve mTLS Kesintisi",
        "description": "SL3 kurumsal güvenlik bölgesinden SL4 yüksek izole veri merkezine taşınan web uygulama sunucularında giden HTTPS/mTLS servis çağrılarının Nutanix Flow güvenlik duvarı oturum tablosunun kilitlenmesi sebebiyle paket düşmesi yaşaması.",
        "methodology": "8d",
        "department": "Bilgi İşlem",
        "industry": "Kurumsal IT ve Veri Merkezi",
        "root_cause": "Nutanix Flow Microsegmentation kural setinde SL4 izole vLAN geçişlerinde Calico CNI VXLAN UDP 4789 kapsülleme portlarının kısıtlanması ve MTU paket parçalanması.",
        "corrective_actions": "1. Nutanix Flow vLAN mikro-segmentasyon kurallarına UDP 4789 kuralı eklenecektir.\n2. Calico CNI MTU ayarı 1440 olarak sabitlenecektir.",
        "lessons_learned": "SL3-SL4 izole hatlarında mikro-segmentasyon devreye alınmadan önce CNI kapsülleme testi yapılacak.",
        "severity": 9, "occurrence": 4, "detection": 3,
        "resolution_status": "in_progress",
        "task_status": "in_progress",
        "task_title": "Nutanix Flow kural revizyonu ve Calico CNI MTU 1440 yapılandırması",
        "assignee": "Erkan Kaya (Sistem ve Ağ Yöneticisi)",
        "tags": ["bilgi-işlem", "nutanix", "microsegmentation", "network", "sl4-izolasyon"]
    },
    {
        "title": "VMware ESXi'den Nutanix AHV Migrasyonu Sonrası SAN Storage iSCSI Multipath (MPIO) I/O Darboğazı",
        "description": "Eski VMware ESXi depolama kümesinden Nutanix AHV altyapısına canlı aktarılan veritabanı sanal sunucularında iSCSI LUN path'lerinin teke düşmesi sonucu okuma/yazma throughput değerinin 1800 MB/s'ten 35 MB/s'e gerilemesi.",
        "methodology": "ishikawa",
        "department": "Bilgi İşlem",
        "industry": "Sistem Altyapısı ve Storage",
        "root_cause": "Fibre Channel SAN switch WWN zoning yapılandırmasında AHV Host HBA kartlarının ikinci kanala (Fabric B) maskelenmemesi ve MPIO ALUA sürücüsünün path kilitlenmesi.",
        "corrective_actions": "1. Dual-fabric SAN zoning haritası güncellenecektir.\n2. Host sunucularda ALUA multipath sürücüsü yenilenecektir.",
        "lessons_learned": "Depolama migrasyonlarında SAN zone değişiklikleri script ile çift kontrolden geçirilecek.",
        "severity": 8, "occurrence": 3, "detection": 3,
        "resolution_status": "open",
        "task_status": "todo",
        "task_title": "SAN Fabric WWN Zoning güncellemesi ve ALUA MPIO sürücü ayarı",
        "assignee": "Ahmet Yılmaz (Kıdemli Bulut Mimar)",
        "tags": ["bilgi-işlem", "storage", "vmware", "nutanix", "san-switch"]
    },
    {
        "title": "RHEL 9 Bare-Metal Sunucu Kurulumunda NVMe-oF Hardware RAID Sürücü İmzası ve Boot Lock",
        "description": "SL4 izole bölgesinde yeni kurulan 8 adet RHEL 9 bare-metal PostgreSQL sunucusunda NVMe SSD'lerin Hardware RAID denetleyicisi tarafından Secure Boot imza reddi nedeniyle Kernel Panic vermesi.",
        "methodology": "5why",
        "department": "Bilgi İşlem",
        "industry": "Sunucu Altyapısı ve Linux",
        "root_cause": "NVMe-oF OEM donanım sürücüsünün UEFI Secure Boot MOK (Machine Owner Key) sertifikasının sunucu BIOS listesine kaydolmaması ve Kernel modülünün karantinaya alınması.",
        "corrective_actions": "1. Kickstart ISO imajına DKMS NVMe-oF paketi eklenecektir.\n2. MOK imzası sunucu BIOS listesine yüklenecektir.",
        "lessons_learned": "Bare-metal sunucu kurulum otomasyonlarına donanım uyumluluk matrisi kontrol adımı eklendi.",
        "severity": 8, "occurrence": 3, "detection": 2,
        "resolution_status": "in_progress",
        "task_status": "in_progress",
        "task_title": "Kickstart ISO NVMe-oF sürücü entegrasyonu ve MOK kaydı",
        "assignee": "Deniz Er (IT Ops Manager)",
        "tags": ["bilgi-işlem", "sunucu", "rhel9", "nvme", "bare-metal"]
    },
    {
        "title": "SL3-SL4 Çapraz Domain Controller Active Directory Kerberos Zaman Eşitleme Kayması",
        "description": "SL4 izole bölgesindeki Domain Controller sunucusunun Kerberos biletlerini reddetmesi sonucu sistem yöneticilerinin sunucu oturumu açarken 401 Unauthorized ve Auth Gateway Timeout alması.",
        "methodology": "5why",
        "department": "Bilgi İşlem",
        "industry": "Kimlik Güvenliği ve Dizin Servisleri",
        "root_cause": "SL3 ve SL4 bağımsız NTP zaman sunucuları arasında 410 milisaniyelik saat kayması oluşması ve Kerberos protokolünün 300ms maksimum tolerans sınırını aşması.",
        "corrective_actions": "1. Stratum-1 donanımsal GPS NTP sunucusu kurulacaktır.\n2. Tüm SL3-SL4 DC sunucuları bu NTP kaynağına senkronize edilecektir.",
        "lessons_learned": "Zaman eşitleme sapması 50ms üzerine çıktığında otomatik uyarım mekanizması tanımlanacak.",
        "severity": 9, "occurrence": 2, "detection": 2,
        "resolution_status": "open",
        "task_status": "todo",
        "task_title": "Stratum-1 GPS NTP montajı ve DC zaman senkronizasyonu",
        "assignee": "Erkan Kaya (Sistem ve Ağ Yöneticisi)",
        "tags": ["bilgi-işlem", "active-directory", "kerberos", "ntp", "sl3-sl4"]
    },
    {
        "title": "Reverse Proxy HAProxy Katmanında SL4 Legacy Sunucular İçin TLS 1.3 Handshake Uyumsuzluğu",
        "description": "SL4 dahili ağındaki eski nesil sunucu ve istemcilerin kurumsal reverse proxy üzerinden mikroservislere bağlanırken SSL_ERROR_NO_CYPHER_OVERLAP hatası vermesi ve servis çağrılarının reddedilmesi.",
        "methodology": "8d",
        "department": "Bilgi İşlem",
        "industry": "Siber Güvenlik ve Proxy",
        "root_cause": "HAProxy sertifikasında yalnızca ECDSA Elliptic Curve şifreleme süitinin zorunlu tutulması ve SL4 bölgesindeki legacy istemcilerde RSA 4096-bit fallback desteğinin bulunmaması.",
        "corrective_actions": "1. RSA 4096-bit fallback sertifikası HAProxy kümesine yüklenecektir.\n2. TLS 1.2/1.3 dual-handshake desteği aktif edilecektir.",
        "lessons_learned": "Eski nesil SL4 istemcileri için cipher suite uyumluluk matrisi yayınlanacak.",
        "severity": 8, "occurrence": 3, "detection": 2,
        "resolution_status": "in_progress",
        "task_status": "in_progress",
        "task_title": "HAProxy dual-certificate RSA/ECDSA kurulumu ve TLS 1.2 desteği",
        "assignee": "Burak Öz (Kıdemli Backend Geliştirici)",
        "tags": ["bilgi-işlem", "haproxy", "tls", "reverse-proxy", "sl4-izolasyon"]
    }
]

async def add_pool_records():
    print("=== ADDING 5 OPEN IT RECORDS TO PROBLEM POOL ===")
    async with async_session_factory() as session:
        user_stmt = select(User).where(User.email == "admin@proby.ai")
        user_res = await session.execute(user_stmt)
        user = user_res.scalars().first()

        user_id = str(user.id) if user else str(uuid.uuid4())

        qdrant_repo = QdrantRepository(vector_size=3072)
        gemini_client = GeminiClient(settings.gemini_api_key, settings.gemini_llm_model, "models/gemini-embedding-001")
        embedding_service = EmbeddingService(client=gemini_client)
        pipeline = EmbeddingPipeline(embedding_service=embedding_service, qdrant_repository=qdrant_repo)

        now = datetime.now(timezone.utc)

        for idx, scenario in enumerate(POOL_SCENARIOS, 1):
            created_at = now - timedelta(hours=idx * 3)

            chat_history = [
                {
                    "role": "assistant",
                    "content": f"👋 Merhaba! **{scenario['department']}** departmanı bünyesinde **\"{scenario['title']}\"** başlıklı problem oturumu başlatıldı.\n\nİnceleme Modülü: **{scenario['methodology'].upper()} Metodolojisi**\n\n📌 **Problem Tanımı**: {scenario['description']}\n\nLütfen saha gözlemlerinizi ve ilk teknik bulguları paylaşın."
                },
                {
                    "role": "user",
                    "content": f"Saha ekibi ve teknik uzmanımız ({scenario['assignee']}) ile detaylı inceleme gerçekleştirdik. Yapılan analiz sonucunda kök nedenin **\"{scenario['root_cause']}\"** olduğu kesinleşti."
                },
                {
                    "role": "assistant",
                    "content": f"🛠️ **Kök Neden Doğrulandı ve Sentezlendi!**\n\n**Kök Neden**: {scenario['root_cause']}\n\nVaka **Problem Havuzu'na (DevOps Board)** aktarıldı. Sorumlu: **{scenario['assignee']}**"
                }
            ]

            step_responses = {
                "step_1": f"{scenario['department']} biriminde vaka incelemesi başlatıldı.",
                "step_2": f"Kök neden olarak tespit edildi: {scenario['root_cause']}"
            }

            prob_session = ProblemSession(
                id=str(uuid.uuid4()),
                owner_id=user_id,
                problem_description=scenario["description"],
                methodology=scenario["methodology"],
                status="pool",
                step_responses=step_responses,
                agent_chat_history=chat_history,
                created_at=created_at,
                updated_at=created_at
            )
            session.add(prob_session)
            await session.flush()

            rpn_val = scenario["severity"] * scenario["occurrence"] * scenario["detection"]
            prob_record = ProblemRecordORM(
                id=str(uuid.uuid4()),
                session_id=prob_session.id,
                user_id=user_id,
                title=scenario["title"],
                description=scenario["description"],
                methodology=scenario["methodology"],
                department=scenario["department"],
                industry=scenario["industry"],
                root_cause=scenario["root_cause"],
                corrective_actions=scenario["corrective_actions"],
                lessons_learned=scenario["lessons_learned"],
                resolution_status=scenario["resolution_status"],
                severity=scenario["severity"],
                occurrence=scenario["occurrence"],
                detection=scenario["detection"],
                rpn=rpn_val,
                yokoten_applied=False,
                embedding_status=EmbeddingStatus.COMPLETED,
                tags=scenario["tags"],
                closure_checklist={
                    "yokoten_scope": "Henüz Problem Havuzu aşamasında, tamamlanınca yaygınlaştırılacaktır.",
                    "checklist": [
                        f"{scenario['methodology'].upper()} Kök Neden Analizi Tamamlandı",
                        "Problem Havuzuna Aktarıldı ve Sorumlu Atandı"
                    ]
                },
                methodology_data=step_responses,
                meta_data={
                    "assignee_name": scenario["assignee"],
                    "rca_chat_history": chat_history
                },
                created_at=created_at,
                updated_at=created_at
            )
            session.add(prob_record)
            await session.flush()

            task = Task(
                id=str(uuid.uuid4()),
                problem_record_id=prob_record.id,
                session_id=prob_session.id,
                title=f"[{scenario['department']}] {scenario['task_title']}",
                status=scenario["task_status"],
                assignee_name=scenario["assignee"],
                created_at=created_at,
                updated_at=created_at
            )
            session.add(task)

            try:
                pipeline.process(
                    record_id=prob_record.id,
                    text=f"{prob_record.title} {prob_record.description} {prob_record.root_cause}",
                    payload={
                        "title": prob_record.title,
                        "description": prob_record.description,
                        "root_cause": prob_record.root_cause,
                        "corrective_actions": prob_record.corrective_actions,
                        "lessons_learned": prob_record.lessons_learned,
                        "department": prob_record.department,
                        "industry": prob_record.industry,
                        "methodology": prob_record.methodology,
                        "severity": prob_record.severity,
                        "occurrence": prob_record.occurrence,
                        "detection": prob_record.detection,
                        "rpn": prob_record.rpn,
                        "resolution_status": prob_record.resolution_status
                    }
                )
            except Exception as e:
                print(f"Warning: Vector index failed for record {prob_record.id}: {e}")

            print(f"[{idx}/5] Added Pool Record: {scenario['title']} ({scenario['resolution_status']})")

        await session.commit()
        print("SUCCESSFULLY ADDED 5 OPEN IT RECORDS TO PROBLEM POOL AND QDRANT")

if __name__ == "__main__":
    asyncio.run(add_pool_records())
