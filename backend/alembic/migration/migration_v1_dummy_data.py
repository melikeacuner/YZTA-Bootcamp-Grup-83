"""seed comprehensive demo data for presentation covering all features

Revision ID: migration_v1_dummy_data
Revises: 
Create Date: 2026-07-31 15:45:00.000000

"""
from typing import Sequence, Union
import uuid
import json
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'migration_v1_dummy_data'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed UUIDs for clean rollback and cross-referencing
DEMO_USER_ID = "11111111-1111-1111-1111-111111111111"

SESSION_1_ID = "22222222-2222-2222-2222-222222222221"
SESSION_2_ID = "22222222-2222-2222-2222-222222222222"
SESSION_3_ID = "22222222-2222-2222-2222-222222222223"
SESSION_4_ID = "22222222-2222-2222-2222-222222222224"
SESSION_5_ID = "22222222-2222-2222-2222-222222222225"
SESSION_6_ID = "22222222-2222-2222-2222-222222222226"
SESSION_7_ID = "22222222-2222-2222-2222-222222222227"
SESSION_8_ID = "22222222-2222-2222-2222-222222222228"
SESSION_9_ID = "22222222-2222-2222-2222-222222222229"
SESSION_10_ID = "22222222-2222-2222-2222-222222222230"

RECORD_1_ID = "33333333-3333-3333-3333-333333333331"
RECORD_2_ID = "33333333-3333-3333-3333-333333333332"
RECORD_3_ID = "33333333-3333-3333-3333-333333333333"
RECORD_4_ID = "33333333-3333-3333-3333-333333333334"
RECORD_5_ID = "33333333-3333-3333-3333-333333333335"
RECORD_6_ID = "33333333-3333-3333-3333-333333333336"
RECORD_7_ID = "33333333-3333-3333-3333-333333333337"
RECORD_8_ID = "33333333-3333-3333-3333-333333333338"
RECORD_9_ID = "33333333-3333-3333-3333-333333333339"
RECORD_10_ID = "33333333-3333-3333-3333-333333333340"

TASK_1_ID = "44444444-4444-4444-4444-444444444441"
TASK_2_ID = "44444444-4444-4444-4444-444444444442"
TASK_3_ID = "44444444-4444-4444-4444-444444444443"
TASK_4_ID = "44444444-4444-4444-4444-444444444444"
TASK_5_ID = "44444444-4444-4444-4444-444444444445"
TASK_6_ID = "44444444-4444-4444-4444-444444444446"
TASK_7_ID = "44444444-4444-4444-4444-444444444447"
TASK_8_ID = "44444444-4444-4444-4444-444444444448"
TASK_9_ID = "44444444-4444-4444-4444-444444444449"

def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=False), # constraint removed in later migration, we won't create unique initially here to match or we just create it clean
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False, server_default="Kullanici"),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Problem Sessions table
    op.create_table(
        "problem_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("methodology", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("current_step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("problem_description", sa.Text, nullable=False),
        sa.Column("step_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("step_responses", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("tags", sa.JSON, nullable=True, server_default="[]"),
        sa.Column("followup_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("assignee_name", sa.String(255), nullable=True),
        sa.Column("tracker_name", sa.String(255), nullable=True),
        sa.Column("agent_chat_history", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("agent_status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Problem Records table
    op.create_table(
        "problem_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problem_sessions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("methodology", sa.String(20), nullable=False),
        sa.Column("methodology_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("step_responses", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("root_cause", sa.Text, nullable=True),
        sa.Column("corrective_actions", sa.Text, nullable=True),
        sa.Column("lessons_learned", sa.Text, nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("problem_category", sa.String(100), nullable=True),
        sa.Column("tags", sa.JSON, nullable=True, server_default="[]"),
        sa.Column("severity", sa.Integer, nullable=True, server_default="1"),
        sa.Column("occurrence", sa.Integer, nullable=True, server_default="1"),
        sa.Column("detection", sa.Integer, nullable=True, server_default="1"),
        sa.Column("rpn", sa.Integer, nullable=True, server_default="1"),
        sa.Column("yokoten_applied", sa.Boolean, nullable=True, server_default="false"),
        sa.Column("closure_checklist", sa.JSON, nullable=True, server_default="{}"),
        sa.Column("resolution_status", sa.String(20), nullable=False, server_default="closed"),
        sa.Column("resolution_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meta_data", sa.JSON, nullable=True, server_default="{}"),
        sa.Column("embedding_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Tasks table
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("problem_record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problem_records.id", ondelete="CASCADE"), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problem_sessions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("assignee_name", sa.String(255), nullable=True),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="todo"),
        sa.Column("proof_description", sa.Text, nullable=True),
        sa.Column("proof_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Embedding Queue table
    op.create_table(
        "embedding_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problem_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Audit Logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("before_state", sa.JSON, nullable=True),
        sa.Column("after_state", sa.JSON, nullable=True),
        sa.Column("before_values", sa.JSON, nullable=True),
        sa.Column("after_values", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    conn = op.get_bind()

    # 1. Insert admin user
    conn.execute(
        sa.text(
            "INSERT INTO users (id, email, hashed_password, full_name, role, is_active) "
            "VALUES (:id, 'admin@proby.ai', :pass, 'Admin Yöneticisi', 'admin', true)"
        ),
        {
            "id": DEMO_USER_ID,
            "pass": "$2b$12$x.cBR5mjMUyr36I0q1eW.uEHtAZtUtSkToldcfuxJDUL0iUy.louG"
        }
    )

    user_id = DEMO_USER_ID

    # 2. Seed Problem Sessions (Aktif, Havuz ve Tamamlanmış seanslar)
    sessions_data = [
        {
            "id": SESSION_1_ID,
            "owner_id": user_id,
            "methodology": "ishikawa",
            "status": "completed",
            "current_step": 5,
            "problem_description": "Otomotiv plastik parça üretim hattında 3 nolu enjeksiyon makinesinde kalıplanan parçalarda kenar çapaklanması ve boyut tolerans sapması gözlemlendi.",
            "step_data": json.dumps({"answers": {"machine": "Hidrolik basınç düşüşü", "method": "Sıcaklık ayar sapması"}}),
            "step_responses": json.dumps({"Makine (Machine)": "Hidrolik kapama valfinde aşınma", "Metot (Method)": "Sıcaklık set değeri sapmış"}),
            "department": "Kalite",
            "summary": "Enjeksiyon kalıplama çapak kusuru kök neden çözümü.",
            "tags": json.dumps(["enjeksiyon", "plastik", "çapak", "ishikawa"]),
            "agent_status": "closed"
        },
        {
            "id": SESSION_2_ID,
            "owner_id": user_id,
            "methodology": "5why",
            "status": "pool",
            "current_step": 5,
            "problem_description": "Ödeme ve sipariş onay mikroservisinde yoğun saatlerde (14:00 - 16:00) ortalama yanıt süresi 45ms'den 450ms'ye yükseliyor, zaman aşımı hataları oluşuyor.",
            "step_data": json.dumps({"answers": {"why1": "DB bağlantıları tıkanıyor", "why2": "Max connection limitine ulaşıldı"}}),
            "step_responses": json.dumps({"1. Neden": "Sorgu süreleri uzuyor", "2. Neden": "DB indeks eksikliği yüzünden tam tablo taraması yapılıyor"}),
            "department": "Bilgi İşlem",
            "summary": "Mikroservis API Yanıt Süresinde Gecikme Spaykı",
            "tags": json.dumps(["api", "postgresql", "performance", "5why"]),
            "agent_status": "active"
        },
        {
            "id": SESSION_3_ID,
            "owner_id": user_id,
            "methodology": "8d",
            "status": "completed",
            "current_step": 8,
            "problem_description": "Gıda soğuk zincir lojistik deposunda B-4 alanında sıcaklık 4°C olması gerekirken 9.5°C'ye yükseldi. Alarm sistemi gecikmeli devreye girdi.",
            "step_data": json.dumps({"answers": {"d1": "Ekip kuruldu", "d2": "Problem tanımlandı"}}),
            "step_responses": json.dumps({"D4 Kök Neden": "PT100 sensör uç korozyonu", "D5 Kalıcı Aksiyon": "IP68 sensör değişimi"}),
            "department": "Lojistik",
            "summary": "Soğuk Depo Sıcaklık Sensörü Sapması",
            "tags": json.dumps(["soğuk-depo", "sensör", "8d", "lojistik"]),
            "agent_status": "closed"
        },
        {
            "id": SESSION_4_ID,
            "owner_id": user_id,
            "methodology": "5why",
            "status": "pool",
            "current_step": 5,
            "problem_description": "Üretim hattında KUKA robotik kol her 200 döngüde bir konum kalibrasyon sapması vererek acil duruşa geçiyor.",
            "step_data": json.dumps({"answers": {"why1": "Eksen 3 servo motor ısınması", "why2": "Redüktör yağı seviye düşüklüğü"}}),
            "step_responses": json.dumps({"1. Neden": "Servo sensör hatalı sinyal üretiyor", "2. Neden": "Redüktör dişli boşluğu standart dışı"}),
            "department": "Üretim",
            "summary": "Robotik kol kalibrasyon sapması",
            "tags": json.dumps(["robotik", "kalibrasyon", "servo", "kuka"]),
            "agent_status": "active"
        },
        {
            "id": SESSION_5_ID,
            "owner_id": user_id,
            "methodology": "pdca",
            "status": "active",
            "current_step": 2,
            "problem_description": "Finans mutabakat modülünde fatura eşleştirme işlemlerinde %3 oranında veri uyuşmazlığı tespit edildi.",
            "step_data": json.dumps({"answers": {"plan": "Fatura OCR algoritması yeniden eğitilecek", "do": "Test verisetinde çalıştırılıyor"}}),
            "step_responses": json.dumps({"Plan": "OCR algoritma güncellemesi", "Do": "Model canlı testi"}),
            "department": "Finans",
            "summary": "Fatura eşleştirme OCR uyuşmazlığı",
            "tags": json.dumps(["finans", "fatura", "ocr", "pdca"]),
            "agent_status": "active"
        },
        {
            "id": SESSION_6_ID,
            "owner_id": user_id,
            "methodology": "agent",
            "status": "completed",
            "current_step": 4,
            "problem_description": "Montaj hattı 2. stasyonda tork tabancası kalibrasyon kayması nedeniyle vida sıkma moment sapması.",
            "step_data": json.dumps({"answers": {"agent_analysis": "Tork sensörü kalibre edildi"}}),
            "step_responses": json.dumps({"Yapay Zeka Teşhisi": "Sensör pülverizasyonu ve kalibrasyon kilit hatası"}),
            "department": "Üretim",
            "summary": "Tork tabancası moment sapması",
            "tags": json.dumps(["tork", "montaj", "kalibrasyon", "agent"]),
            "agent_status": "closed"
        },
        {
            "id": SESSION_7_ID,
            "owner_id": user_id,
            "methodology": "ishikawa",
            "status": "completed",
            "current_step": 5,
            "problem_description": "CNC Freze Tezgahı Mil Yatağında Aşırı Isınma ve Titreşim",
            "step_data": json.dumps({"answers": {"machine": "Rulman yağsızlaşması"}}),
            "step_responses": json.dumps({"Makine": "Spindle rulman gresi kuruma yapmış"}),
            "department": "Üretim",
            "summary": "CNC Spindle aşırı ısınması kök neden çözümü.",
            "tags": json.dumps(["cnc", "spindle", "rulman", "bakım"]),
            "agent_status": "closed"
        },
        {
            "id": SESSION_8_ID,
            "owner_id": user_id,
            "methodology": "5why",
            "status": "completed",
            "current_step": 5,
            "problem_description": "Depo OTM Konveyör Bant Motoru Sıkışması ve Paket Birikmesi",
            "step_data": json.dumps({"answers": {"why1": "Bant gergisi gevşedi"}}),
            "step_responses": json.dumps({"1. Neden": "Bant gergisi gevşedi"}),
            "department": "Lojistik",
            "summary": "Konveyör bant sıkışması analizi.",
            "tags": json.dumps(["konveyör", "lojistik", "bant", "sevkiyat"]),
            "agent_status": "closed"
        },
        {
            "id": SESSION_9_ID,
            "owner_id": user_id,
            "methodology": "pdca",
            "status": "completed",
            "current_step": 4,
            "problem_description": "ERP Fatura ve Stok Mutabakatında Sentetik Kur Farkı Sapması",
            "step_data": json.dumps({"answers": {"plan": "Kur API retry entegrasyonu"}}),
            "step_responses": json.dumps({"Plan": "Retry & Fallback kur API entegrasyonu"}),
            "department": "Finans",
            "summary": "Döviz kuru fatura aktarım sapması.",
            "tags": json.dumps(["finans", "erp", "kur", "tcmb"]),
            "agent_status": "closed"
        },
        {
            "id": SESSION_10_ID,
            "owner_id": user_id,
            "methodology": "8d",
            "status": "completed",
            "current_step": 8,
            "problem_description": "Boyahane Test Standında Mikron Kalınlık Sapması ve Yüzey Pürüzlülüğü",
            "step_data": json.dumps({"answers": {"d4": "Voltaj kaskad arızası"}}),
            "step_responses": json.dumps({"D4": "Tabanca jeneratör voltajı kaymış"}),
            "department": "Kalite",
            "summary": "Elektrostatik boya mikron sapması çözümü.",
            "tags": json.dumps(["boyahane", "mikron", "kalite", "8d"]),
            "agent_status": "closed"
        }
    ]

    for s in sessions_data:
        conn.execute(
            sa.text(
                "INSERT INTO problem_sessions (id, owner_id, methodology, status, current_step, problem_description, step_data, step_responses, department, summary, tags, agent_status) "
                "VALUES (:id, :owner_id, :methodology, :status, :current_step, :problem_description, :step_data, :step_responses, :department, :summary, :tags, :agent_status) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            s
        )

    # 3. Seed Problem Records
    records_data = [
        {
            "id": RECORD_1_ID,
            "session_id": SESSION_1_ID,
            "user_id": user_id,
            "title": "Enjeksiyon Kalıplama Plastik Parçada Çapak Kusuru",
            "description": "Otomotiv plastik parça üretim hattında 3 nolu enjeksiyon makinesinde kalıplanan parçalarda kenar çapaklanması ve boyut tolerans sapması gözlemlendi. Hata oranı %4.5 seviyesine çıktı.",
            "methodology": "ishikawa",
            "methodology_data": json.dumps({"Makine": "Hidrolik basınç kaybı", "Metot": "Sıcaklık sapması"}),
            "step_responses": json.dumps({"Makine": "Hidrolik basınç kaybı", "Metot": "Sıcaklık sapması"}),
            "root_cause": "Kalıp kapama basıncının hidrolik valf aşınması nedeniyle 180 bardan 145 bara düşmesi ve eriyik sıcaklığının 230°C yerine 245°C çalıştırılması.",
            "corrective_actions": "1. Hidrolik kapama valfi yenilendi.\n2. Kalıp sıcaklık kontrol cihazı kalibre edildi ve 225°C standart set değerine alındı.",
            "lessons_learned": "Kök Neden: Hidrolik valf basınç kaybı.\nDüzeltici Eylemler: Valf değişimi ve kalibrasyon yapıldı.\nSonuç: Çapak kusur oranı %4.5'ten %0.1'e düşürüldü.\nÖnleyici Öneriler: Periyodik hidrolik denetim 500 saate çekildi.",
            "industry": "Otomotiv İmalatı",
            "department": "Kalite",
            "problem_category": "Kalite Hatası",
            "tags": json.dumps(["enjeksiyon", "plastik", "çapak", "ishikawa"]),
            "severity": 7,
            "occurrence": 5,
            "detection": 3,
            "rpn": 105,
            "yokoten_applied": True,
            "resolution_status": "closed",
            "embedding_status": "completed",
            "meta_data": json.dumps({
                "assignee_name": "Ahmet Yılmaz (Kalite Uzmanı)",
                "tracker_name": "Mehmet Demir (Üretim Müdürü)",
                "closed_at": datetime.utcnow().isoformat(),
                "documents": [
                    {
                        "id": "doc-101",
                        "filename": "kalip_basinc_olcum_raporu.pdf",
                        "file_type": "application/pdf",
                        "summary": "Hidrolik basınç 145 barda sabitlenmiş, valf sızdırmazlık contalarında yıpranma tespit edilmiştir.",
                        "uploaded_at": datetime.utcnow().isoformat()
                    }
                ]
            })
        },
        {
            "id": RECORD_2_ID,
            "session_id": SESSION_2_ID,
            "user_id": user_id,
            "title": "Mikroservis API Yanıt Süresinde 450ms Gecikme Spaykı",
            "description": "Ödeme ve sipariş onay mikroservisinde yoğun saatlerde (14:00 - 16:00) ortalama yanıt süresi 45ms'den 450ms'ye yükseliyor, zaman aşımı hataları oluşuyor.",
            "methodology": "5why",
            "methodology_data": json.dumps({"1. Neden": "Sorgu süresi uzun", "2. Neden": "DB indeks eksik"}),
            "step_responses": json.dumps({"1. Neden": "Sorgu süresi uzun", "2. Neden": "DB indeks eksik"}),
            "root_cause": "Veritabanı bağlantı havuzunun (max_connections=20) yetersiz olması ve orders tablosundaki eksik indeks nedeniyle sorguların Sequential Scan yapması.",
            "corrective_actions": "1. PostgreSQL indeksi eklenecek.\n2. Connection pool 50'ye çıkarılacak ve Redis entegre edilecek.",
            "lessons_learned": "Kök Neden: Indeks eksikliği ve dar bağlantı havuzu.",
            "industry": "Yazılım / E-Ticaret",
            "department": "Bilgi İşlem",
            "problem_category": "Diğer",
            "tags": json.dumps(["api", "postgresql", "performance", "5why"]),
            "severity": 6,
            "occurrence": 6,
            "detection": 2,
            "rpn": 72,
            "yokoten_applied": False,
            "resolution_status": "open",
            "embedding_status": "completed",
            "meta_data": json.dumps({
                "assignee_name": "Burak Öz (Kıdemli Backend Geliştirici)",
                "tracker_name": "Selin Arslan (Software Lead)",
                "conversation_summary": "1. DB indeksi eklenmesi kararlaştırıldı.\n2. Connection pool boyutu 50'ye yükseltildi.\n3. Redis önbellek katmanı entegrasyonu devam ediyor.",
                "documents": [
                    {
                        "id": "doc-201",
                        "filename": "pg_stat_statements_logs.txt",
                        "file_type": "text/plain",
                        "summary": "orders tablosundaki user_id sorgularında Sequential Scan tespit edildi. Indeks eklenmesi yanıt süresini %90 düşürecektir.",
                        "uploaded_at": datetime.utcnow().isoformat()
                    }
                ],
                "resolution_chat_history": [
                    {
                        "role": "assistant",
                        "content": "👋 Merhaba! Kök neden tespit edildi: DB bağlantı havuzu ve indeks eksikliği. Hangi aksiyon adımları ile başlamak istersiniz?"
                    },
                    {
                        "role": "user",
                        "content": "orders tablosuna user_id ve created_at indeksi eklemeyi planlıyoruz."
                    },
                    {
                        "role": "assistant",
                        "content": "Mükemmel! `CREATE INDEX idx_orders_user_created ON orders(user_id, created_at DESC)` indeksi sorgu süresini 450ms'den 20ms seviyesine düşürecektir. Ayrıca Redis önbellek katmanı ekleyebiliriz."
                    }
                ]
            })
        },
        {
            "id": RECORD_3_ID,
            "session_id": SESSION_3_ID,
            "user_id": user_id,
            "title": "Soğuk Depo Sıcaklık Sensörü Sapması ve Kompresör Isınması",
            "description": "Gıda soğuk zincir lojistik deposunda B-4 alanında sıcaklık 4°C olması gerekirken 9.5°C'ye yükseldi. Alarm sistemi gecikmeli devreye girdi.",
            "methodology": "8d",
            "methodology_data": json.dumps({"D4": "Sensör oksitlenmesi"}),
            "step_responses": json.dumps({"D4": "Sensör oksitlenmesi"}),
            "root_cause": "PT100 sıcaklık sensör uçlarının nem korozyonuna uğrayarak direnç değerinin kayması ve kondanser filtrelerinin tıkanması.",
            "corrective_actions": "1. IP68 paslanmaz sensör takıldı.\n2. Filtreler temizlendi ve otomatik bakım takvimine alındı.",
            "lessons_learned": "Kök Neden: Sensör oksitlenmesi.\nDüzeltici Eylemler: IP68 sensör montajı yapıldı.\nSonuç: Sıcaklık kararlılığı ±0.5°C aralığına getirildi.",
            "industry": "Gıda Lojistiği",
            "department": "Lojistik",
            "problem_category": "Lojistik Gecikme",
            "tags": json.dumps(["soğuk-depo", "sensör", "8d", "lojistik"]),
            "severity": 8,
            "occurrence": 3,
            "detection": 4,
            "rpn": 96,
            "yokoten_applied": True,
            "resolution_status": "closed",
            "embedding_status": "completed",
            "meta_data": json.dumps({
                "assignee_name": "Fatma Şahin (Tesis Sorumlusu)",
                "tracker_name": "Caner Kaya (Operasyon Direktörü)",
                "closed_at": datetime.utcnow().isoformat()
            })
        },
        {
            "id": RECORD_4_ID,
            "session_id": SESSION_4_ID,
            "user_id": user_id,
            "title": "Üretim Hattı Robotik Kol Kalibrasyon Sapması",
            "description": "Üretim hattında KUKA robotik kol her 200 döngüde bir konum kalibrasyon sapması vererek acil duruşa geçiyor.",
            "methodology": "5why",
            "methodology_data": json.dumps({"1. Neden": "Servo sinyal hatası"}),
            "step_responses": json.dumps({"1. Neden": "Servo sinyal hatası"}),
            "root_cause": "Eksen 3 servo motor dişli boşluğu ve yağ seviyesindeki azalma.",
            "corrective_actions": "1. Redüktör yağı değişimi yapılacak.\n2. Servo motor enkoder kalibrasyonu tekrarlanacak.",
            "lessons_learned": "Kök Neden: Servo motor dişli boşluğu.",
            "industry": "Otomotiv İmalatı",
            "department": "Üretim",
            "problem_category": "Kalite Hatası",
            "tags": json.dumps(["robotik", "kalibrasyon", "servo", "kuka"]),
            "severity": 6,
            "occurrence": 4,
            "detection": 3,
            "rpn": 72,
            "yokoten_applied": False,
            "resolution_status": "open",
            "embedding_status": "completed",
            "meta_data": json.dumps({
                "assignee_name": "Mehmet Can (Bakım Mühendisi)",
                "tracker_name": "Hasan Kaya (Bakım Şefi)",
                "conversation_summary": "1. Redüktör yağının yenilenmesi kararlaştırıldı.\n2. Enkoder sıfırlama prosedürü işletilecek.",
                "documents": [
                    {
                        "id": "doc-401",
                        "filename": "kuka_robot_bakim_raporu.pdf",
                        "file_type": "application/pdf",
                        "summary": "Eksen 3 servo motor enkoderinde 0.4 derecelik sapma ve yağ vizkozite kaybı saptandı.",
                        "uploaded_at": datetime.utcnow().isoformat()
                    }
                ],
                "resolution_chat_history": [
                    {
                        "role": "assistant",
                        "content": "👋 Merhaba! KUKA robotik kol kalibrasyon sapması problemi için servis dokümanı incelendi. Hangi düzeltici eylemi uygulamak istersiniz?"
                    },
                    {
                        "role": "user",
                        "content": "Redüktör yağını sentetik yağ ile yenileyip enkoder kalibrasyonunu tekrarlayacağız."
                    }
                ]
            })
        },
        {
            "id": RECORD_5_ID,
            "session_id": SESSION_6_ID,
            "user_id": user_id,
            "title": "Montaj Hattı Tork Tabancası Moment Sapması",
            "description": "Montaj hattı 2. stasyonda tork tabancası kalibrasyon kayması nedeniyle vida sıkma moment sapması.",
            "methodology": "agent",
            "methodology_data": json.dumps({"AI": "Sensör pülverizasyon hatası"}),
            "step_responses": json.dumps({"AI": "Sensör pülverizasyon hatası"}),
            "root_cause": "Pnömatik basınç regülatörü filtresinin tıkanarak anlık hava basıncını 6 bardan 4.2 bara düşürmesi.",
            "corrective_actions": "1. Regülatör filtresi değiştirildi.\n2. Dijital tork kalibratörü ile doğrulandı.",
            "lessons_learned": "Kök Neden: Pnömatik filtre tıkanması.\nDüzeltici Eylemler: Filtre değişimi yapıldı.",
            "industry": "İmalat",
            "department": "Üretim",
            "problem_category": "Kalite Hatası",
            "tags": json.dumps(["tork", "montaj", "kalibrasyon"]),
            "severity": 5,
            "occurrence": 3,
            "detection": 2,
            "rpn": 30,
            "yokoten_applied": True,
            "resolution_status": "closed",
            "embedding_status": "completed",
            "meta_data": json.dumps({
                "assignee_name": "Kadir Şen",
                "tracker_name": "Hasan Kaya",
                "closed_at": datetime.utcnow().isoformat()
            })
        },
        {
            "id": RECORD_6_ID,
            "session_id": SESSION_7_ID,
            "user_id": user_id,
            "title": "CNC Freze Tezgahı Mil Yatağında Aşırı Isınma ve Titreşim",
            "description": "Üretim tesisindeki CNC-04 tezgahında kesici mil 12.000 devir/dakikada çalışırken mil yatağı sıcaklığı 85°C'ye ulaştı ve eksen titreşim alarmı verdi.",
            "methodology": "ishikawa",
            "methodology_data": json.dumps({"Makine": "Rulman yağsızlaşması", "Bakım": "Yağlama periyodu aşılmış"}),
            "step_responses": json.dumps({"Makine": "Spindle rulman gresi kuruma yapmış"}),
            "root_cause": "Otomatik greslama pompası selonoid valfinin tıkanması nedeniyle rulman yatağının 40 saat yağsız çalışması.",
            "corrective_actions": "1. Spindle rulman seti seramik rulman ile yenilendi.\n2. Otomatik yağlama hattına basınç sensörü eklendi.",
            "lessons_learned": "Kök Neden: Greslama valf tıkanması.\nDüzeltici Eylemler: Seramik rulman takıldı.",
            "industry": "Talaşlı İmalat",
            "department": "Üretim",
            "problem_category": "Makine Arızası",
            "tags": json.dumps(["cnc", "spindle", "rulman", "bakım"]),
            "severity": 9,
            "occurrence": 7,
            "detection": 4,
            "rpn": 252,
            "yokoten_applied": True,
            "resolution_status": "closed",
            "embedding_status": "completed",
            "meta_data": json.dumps({
                "assignee_name": "Mehmet Can (Bakım Mühendisi)",
                "tracker_name": "Hasan Kaya",
                "closed_at": datetime.utcnow().isoformat()
            })
        },
        {
            "id": RECORD_7_ID,
            "session_id": SESSION_8_ID,
            "user_id": user_id,
            "title": "Depo OTM Konveyör Bant Motoru Sıkışması ve Paket Birikmesi",
            "description": "Lojistik ana dağıtım merkezinde A-2 konveyör hattında bant sıkışması nedeniyle paket birikmesi ve 2 saatlik sevkiyat duruşu yaşandı.",
            "methodology": "5why",
            "methodology_data": json.dumps({"1. Neden": "Bant gergisi gevşedi", "2. Neden": "Rulman aşınmış"}),
            "step_responses": json.dumps({"1. Neden": "Bant gergisi gevşedi"}),
            "root_cause": "Konveyör tahrik kasnağındaki kauçuk kaplamanın yıpranarak bandın kaçırmasına neden olması.",
            "corrective_actions": "1. Tahrik kasnağı vuruk ve vulcanize kaplaması yenilendi.\n2. Gergi tamburu hizalandı.",
            "lessons_learned": "Kök Neden: Kasnak kaplama yıpranması.",
            "industry": "Lojistik",
            "department": "Lojistik",
            "problem_category": "Lojistik Gecikme",
            "tags": json.dumps(["konveyör", "lojistik", "bant", "sevkiyat"]),
            "severity": 8,
            "occurrence": 5,
            "detection": 3,
            "rpn": 120,
            "yokoten_applied": False,
            "resolution_status": "closed",
            "embedding_status": "completed",
            "meta_data": json.dumps({
                "assignee_name": "Fatma Şahin (Tesis Sorumlusu)",
                "tracker_name": "Caner Kaya",
                "closed_at": datetime.utcnow().isoformat()
            })
        },
        {
            "id": RECORD_8_ID,
            "session_id": SESSION_9_ID,
            "user_id": user_id,
            "title": "ERP Fatura ve Stok Mutabakatında Sentetik Kur Farkı Sapması",
            "description": "Finans ERP sistemi dövizli fatura aktarımında TCMB kur servisinin anlık zaman aşımına uğraması sonucu %0.8 hatalı kur kaydı alındı.",
            "methodology": "pdca",
            "methodology_data": json.dumps({"Plan": "Kur servisine retry mekanizması ekle", "Do": "Fallback servisi yazıldı"}),
            "step_responses": json.dumps({"Plan": "Retry & Fallback kur API entegrasyonu"}),
            "root_cause": "Döviz kurları çekilirken timeout durumunda varsayılan sabit değer atanması.",
            "corrective_actions": "1. Kur servisine 3 tekrarlı retry ve yedek API fallback servisi bağlandı.\n2. Hatalı 14 fatura düzeltildi.",
            "lessons_learned": "Kök Neden: API timeout yönetimi eksikliği.",
            "industry": "Finans",
            "department": "Finans",
            "problem_category": "Veri Hatası",
            "tags": json.dumps(["finans", "erp", "kur", "tcmb"]),
            "severity": 4,
            "occurrence": 2,
            "detection": 2,
            "rpn": 16,
            "yokoten_applied": True,
            "resolution_status": "closed",
            "embedding_status": "completed",
            "meta_data": json.dumps({
                "assignee_name": "Selin Arslan",
                "tracker_name": "Burak Öz",
                "closed_at": datetime.utcnow().isoformat()
            })
        },
        {
            "id": RECORD_9_ID,
            "session_id": SESSION_10_ID,
            "user_id": user_id,
            "title": "Boyahane Test Standında Mikron Kalınlık Sapması ve Yüzey Pürüzlülüğü",
            "description": "Otomotiv yan sanayi boyahanesinde elektrostatik toz boya uygulamasında film kalınlığı 60 mikron yerine 95 mikron ölçüldü.",
            "methodology": "8d",
            "methodology_data": json.dumps({"D4": "Nozul voltaj ayarı yüksek"}),
            "step_responses": json.dumps({"D4": "Tabanca jeneratör voltajı kaymış"}),
            "root_cause": "Boya tabancası yüksek voltaj kaskad ünitesindeki yıpranma nedeniyle koronlama voltajının 80kV yerine 105kV çıkması.",
            "corrective_actions": "1. Volt kaskad ünitesi yenilendi.\n2. Otomatik voltaj kalibrasyon cihazı devreye alındı.",
            "lessons_learned": "Kök Neden: Voltaj kaskad arızası.",
            "industry": "Otomotiv İmalatı",
            "department": "Kalite",
            "problem_category": "Kalite Hatası",
            "tags": json.dumps(["boyahane", "mikron", "kalite", "8d"]),
            "severity": 7,
            "occurrence": 4,
            "detection": 3,
            "rpn": 84,
            "yokoten_applied": True,
            "resolution_status": "closed",
            "embedding_status": "completed",
            "meta_data": json.dumps({
                "assignee_name": "Ahmet Yılmaz",
                "tracker_name": "Mehmet Demir",
                "closed_at": datetime.utcnow().isoformat()
            })
        }
    ]

    for r in records_data:
        conn.execute(
            sa.text(
                "INSERT INTO problem_records (id, session_id, user_id, title, description, methodology, methodology_data, step_responses, root_cause, corrective_actions, lessons_learned, industry, department, problem_category, tags, severity, occurrence, detection, rpn, yokoten_applied, resolution_status, embedding_status, meta_data) "
                "VALUES (:id, :session_id, :user_id, :title, :description, :methodology, :methodology_data, :step_responses, :root_cause, :corrective_actions, :lessons_learned, :industry, :department, :problem_category, :tags, :severity, :occurrence, :detection, :rpn, :yokoten_applied, :resolution_status, :embedding_status, :meta_data) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            r
        )

    # 4. Seed Tasks
    tasks_data = [
        {
            "id": TASK_1_ID,
            "problem_record_id": RECORD_2_ID,
            "session_id": SESSION_2_ID,
            "title": "PostgreSQL orders tablosuna idx_orders_user_created indeksi eklenmesi",
            "description": "API yanıt sürelerini 450ms'den 20ms'ye düşürmek için veritabanı indeksinin canlıya alınması.",
            "assignee_name": "Burak Öz",
            "department": "Bilgi İşlem",
            "priority": "high",
            "status": "in_progress",
            "proof_description": "Staging veritabanında test edildi, EXPLAIN ANALYZE çıktısı alındı.",
            "proof_url": "https://github.com/org/repo/pull/142"
        },
        {
            "id": TASK_2_ID,
            "problem_record_id": RECORD_4_ID,
            "session_id": SESSION_4_ID,
            "title": "KUKA Eksen 3 servo motor redüktör yağı değişimi ve enkoder kalibrasyonu",
            "description": "Robotik kol acil duruşlarını engellemek için bakım müdahalesi.",
            "assignee_name": "Mehmet Can",
            "department": "Üretim",
            "priority": "critical",
            "status": "todo",
            "proof_description": None,
            "proof_url": None
        },
        {
            "id": TASK_3_ID,
            "problem_record_id": RECORD_1_ID,
            "session_id": SESSION_1_ID,
            "title": "Enjeksiyon presi hidrolik valf sızdırmazlık testi ve basınç sabitleme",
            "description": "Çapak kusurunu engellemek için basınç değerinin 180 bara sabitlenmesi.",
            "assignee_name": "Ahmet Yılmaz",
            "department": "Kalite",
            "priority": "medium",
            "status": "completed",
            "proof_description": "Valf basınç test raporu imzalandı ve kalite havuzuna işlendi.",
            "proof_url": "https://internal-docs/kalite/valf_test_report.pdf"
        },
        {
            "id": TASK_4_ID,
            "problem_record_id": RECORD_3_ID,
            "session_id": SESSION_3_ID,
            "title": "Soğuk depo B-4 alanına IP68 muhafazalı PT100 sensör montajı",
            "description": "Gıda soğuk zincir koruması için sensör yenileme.",
            "assignee_name": "Fatma Şahin",
            "department": "Lojistik",
            "priority": "high",
            "status": "completed",
            "proof_description": "Sensör montaj fotoğrafı ve SCADA sıcaklık doğrulama kaydı.",
            "proof_url": "https://internal-docs/lojistik/sensor_montaj.png"
        },
        {
            "id": TASK_5_ID,
            "problem_record_id": RECORD_2_ID,
            "session_id": SESSION_2_ID,
            "title": "Redis bağlantı havuzu sınır ayarlarının 50'ye yükseltilmesi",
            "description": "Bağlantı zaman aşımı hatalarını giderme aksiyonu.",
            "assignee_name": "Burak Öz",
            "department": "Bilgi İşlem",
            "priority": "medium",
            "status": "delayed",
            "proof_description": "Sistem güncellemesi için bakım penceresi bekleniyor.",
            "proof_url": None
        },
        {
            "id": TASK_6_ID,
            "problem_record_id": RECORD_6_ID,
            "session_id": SESSION_7_ID,
            "title": "CNC Spindle seramik rulman montajı ve yağlama hattı sensör testi",
            "description": "CNC mil yatağı aşırı ısınmasını engelleme aksiyonu.",
            "assignee_name": "Mehmet Can",
            "department": "Üretim",
            "priority": "critical",
            "status": "completed",
            "proof_description": "Spindle titreşim ve sıcaklık test verileri onaylandı.",
            "proof_url": "https://internal-docs/uretim/cnc_spindle_test.pdf"
        },
        {
            "id": TASK_7_ID,
            "problem_record_id": RECORD_7_ID,
            "session_id": SESSION_8_ID,
            "title": "Depo A-2 Konveyör tahrik kasnağı vulcanize kaplama değişimi",
            "description": "Bant kaçırma ve sıkışmalarını gidermek için bakım müdahalesi.",
            "assignee_name": "Fatma Şahin",
            "department": "Lojistik",
            "priority": "high",
            "status": "completed",
            "proof_description": "Kasnak değişim servis formu.",
            "proof_url": "https://internal-docs/lojistik/kasnak_bakim.png"
        },
        {
            "id": TASK_8_ID,
            "problem_record_id": RECORD_8_ID,
            "session_id": SESSION_9_ID,
            "title": "ERP Döviz Kuru API servisine retry ve fallback katmanı eklenmesi",
            "description": "Kur farkı veri uyuşmazlığını önlemek için yazılım güncellemesi.",
            "assignee_name": "Selin Arslan",
            "department": "Finans",
            "priority": "medium",
            "status": "in_progress",
            "proof_description": "PR yayında, testler sürdürülüyor.",
            "proof_url": "https://github.com/org/repo/pull/189"
        },
        {
            "id": TASK_9_ID,
            "problem_record_id": RECORD_9_ID,
            "session_id": SESSION_10_ID,
            "title": "Boyahane elektrostatik tabanca voltaj kaskad ünitesi değişimi",
            "description": "Mikron boya kalınlık sapmasını düzeltme aksiyonu.",
            "assignee_name": "Ahmet Yılmaz",
            "department": "Kalite",
            "priority": "high",
            "status": "completed",
            "proof_description": "Kalınlık mikron ölçüm raporu onaylandı.",
            "proof_url": "https://internal-docs/kalite/mikron_rapor.pdf"
        }
    ]

    for t in tasks_data:
        conn.execute(
            sa.text(
                "INSERT INTO tasks (id, problem_record_id, session_id, title, description, assignee_name, department, priority, status, proof_description, proof_url) "
                "VALUES (:id, :problem_record_id, :session_id, :title, :description, :assignee_name, :department, :priority, :status, :proof_description, :proof_url) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            t
        )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("embedding_queue")
    op.drop_table("tasks")
    op.drop_table("problem_records")
    op.drop_table("problem_sessions")
    op.drop_table("users")
