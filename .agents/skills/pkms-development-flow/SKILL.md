---
name: pkms-development-flow
description: Workspace-specific development workflow, architecture overview, and task logging guide for the Problem Knowledge Management System.
---

# PKMS Development Workflow Skill

Bu kılavuz, **YZTA-Bootcamp-Grup-83** projesinin mimarisini, dosya yapısını ve geliştirme standartlarını tanımlar. Bu repoda geliştirme yaparken aşağıdaki yönergelere sıkı sıkıya uyulmalıdır.

## 1. Mimari Genel Bakış

Sistem 3 katmandan oluşur:
1.  **FastAPI Backend**: `backend/app` dizininde bulunur. SQLAlchemy (async) ile PostgreSQL veritabanına ve Qdrant (semantik arama vektör veritabanı) ile Redis (Celery asenkron kuyruğu) servislerine bağlanır.
2.  **Celery Worker**: Asenkron gömme (embedding) kuyruğunu işleyerek Qdrant veritabanını güncel tutar.
3.  **Next.js Frontend**: `frontend/src` dizininde bulunur. SPA (Single Page Application) yapısındadır. Sol tarafta kenar çubuğu (aktif seanslar listesi) ve sağ panelde modüllerin (Yeni Oturum, A3 Rapor Havuzu, Aksiyon Puan Kanban Panosu, Yönetici Dashboardu, Bilgi Bankası) dinamik yüklenmesini sağlar.

## 2. Geliştirme Yönergeleri

### Backend Geliştirme
*   **Modeller**: Yeni bir tablo veya alan ekleneceğinde mutlaka [models.py](file:///C:/Users/sevke/OneDrive/Masaüstü/My%20Dev%20Environment/YZTA-Bootcamp-Grup-83/backend/app/infrastructure/db/models.py) güncellenmeli ve ardından `docker-compose exec backend alembic revision --autogenerate -m "mesaj"` ile migration oluşturulup `docker-compose exec backend alembic upgrade head` ile uygulanmalıdır.
*   **AI Entegrasyonu**: LLM ve yapay zeka ajanı logic'leri sırasıyla [llm_service.py](file:///C:/Users/sevke/OneDrive/Masaüstü/My%20Dev%20Environment/YZTA-Bootcamp-Grup-83/backend/app/services/llm_service.py) ve [agent_service.py](file:///C:/Users/sevke/OneDrive/Masaüstü/My%20Dev%20Environment/YZTA-Bootcamp-Grup-83/backend/app/services/agent_service.py) dosyalarında tutulur. `google-genai` SDK'sının kararlı fonksiyonları tercih edilmelidir.

### Frontend Geliştirme
*   **Sayfa Yönlendirmeleri**: Tüm sistem tek bir SPA arayüzünde çalıştığından, yeni bir sayfa eklemek yerine `/src/components/dashboard.tsx` dosyasında yeni bir sekme (tab) / görünüm (view) ve buna bağlı component tanımlanmalıdır.
*   **Tema Varlıkları**: Renkler, cam paneller (glassmorphism), butonlar ve geçiş efektleri gibi görsel tokenlar [globals.css](file:///C:/Users/sevke/OneDrive/Masaüstü/My%20Dev%20Environment/YZTA-Bootcamp-Grup-83/frontend/src/app/globals.css)'te tanımlıdır. Ad-hoc (rastgele) stillendirmelerden kaçınılmalı, buradaki CSS sınıfları (`btn-primary`, `btn-secondary`, `glass`, `glow-border`) kullanılmalıdır.
*   **Tip Güvenliği**: Yeni veri yapıları ve API yanıtları mutlaka [types.ts](file:///C:/Users/sevke/OneDrive/Masaüstü/My%20Dev%20Environment/YZTA-Bootcamp-Grup-83/frontend/src/lib/types.ts) dosyasına kaydedilmeli ve API istekleri [api.ts](file:///C:/Users/sevke/OneDrive/Masaüstü/My%20Dev%20Environment/YZTA-Bootcamp-Grup-83/frontend/src/lib/api.ts) üzerinden yapılmalıdır.

## 3. Süreç Takibi ve Günlük Kayıtları
Her yeni özellik ekleme veya iyileştirme adımında, yapılan değişiklikler `development_process/` klasörü altında `process_log_<numara>.md` adıyla kronolojik olarak arşivlenmelidir. Bu arşivde aşağıdaki şablon kullanılmalıdır:
*   Gerçekleştirilen Değişikliklerin Amacı
*   Düzenlenen/Eklenen Dosyalar
*   Veritabanı Şema Değişiklikleri (varsa)
*   Doğrulama/Test Aşamaları
