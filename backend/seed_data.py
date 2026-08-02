import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, delete
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models import ProblemSession, ProblemRecordORM, Task, AuditLog, User
from app.domain.enums import SessionStatus, EmbeddingStatus
from app.services.embedding_pipeline import EmbeddingPipeline
from app.services.embedding_service import EmbeddingService
from app.infrastructure.repositories.qdrant_repository import QdrantRepository
from app.core.config import get_settings

settings = get_settings()

DEPARTMENTS = ["Üretim", "Lojistik", "Kalite", "Bilgi İşlem", "Finans"]

DEPARTMENT_PERSONNEL = {
    "Üretim": ["Mehmet Can (Bakım Mühendisi)", "Ali Öztürk (Üretim Sorumlusu)", "Kadir Şen (Montaj Şefi)", "Hasan Kaya (Bakım Şefi)"],
    "Lojistik": ["Fatma Şahin (Tesis Sorumlusu)", "Caner Kaya (Operasyon Direktörü)", "Volkan Aydoğan (Depo Şefi)"],
    "Kalite": ["Ahmet Yılmaz (Kalite Uzmanı)", "Merve Şahin (Kalite Mühendisi)", "Mehmet Demir (Üretim Müdürü)"],
    "Bilgi İşlem": ["Burak Öz (Kıdemli Backend Geliştirici)", "Selin Arslan (Software Lead)", "Ahmet Yılmaz (Kıdemli Bulut Mimar)", "Deniz Er (IT Ops Manager)"],
    "Finans": ["Zeynep Avcı (Mali İşler Uzmanı)", "Emre Yıldız (Finansal Analist)"]
}

SCENARIOS = [
    # --- ÜRETİM (10 Scenarios) ---
    {
        "department": "Üretim",
        "title": "Plastik Enjeksiyon Kalıbında Çapaklanma ve Emiş Basıncı Düşüklüğü",
        "description": "Plastik enjeksiyon üretim hattında 3 nolu kalıpta parçaların kenarlarında aşırı çapaklanma gözlendi. Enjeksiyon emiş basıncı 120 bar seviyesinden 85 bar seviyesine düştü.",
        "methodology": "5why",
        "category": "Makine & Ekipman",
        "industry": "Otomotiv Yan Sanayi",
        "root_cause": "Kalıp ayırma yüzeyindeki hidrolik conta aşınması ve basınç valfinde biriken yağ tortusu basınç kaybına yol açmıştır.",
        "corrective_actions": "1. Hidrolik conta takımı yenilendi.\n2. Enjeksiyon valfi ultraviyole yıkama ile temizlendi.\n3. Basınç sensörleri kalibre edildi.",
        "lessons_learned": "Enjeksiyon valflerinin 500 çalışma saatinde bir ultrasonik temizliği bakım periyoduna eklendi. Çapak kontrolü otomasyon kamerasına bağlandı.",
        "severity": 8, "occurrence": 5, "detection": 4,
        "task_title": "Hidrolik conta değişimi ve valf ultrasonik temizliği",
        "task_status": "completed",
        "assignee": "Mehmet Can (Bakım Mühendisi)"
    },
    {
        "department": "Üretim",
        "title": "CNC Torna Tezgahında Mil Rulmanı Aşınması ve Yüzey Pürüzlülüğü",
        "description": "CNC torna hattında işlenen miller parametre toleranslarını aşarak Ra 3.2 pürüzlülük değerine ulaştı. Yataklarda yüksek frekanslı titreşim tespit edildi.",
        "methodology": "8d",
        "category": "İşleme & Tolerans",
        "industry": "Makine İmalat",
        "root_cause": "Ana mil (spindle) rulmanında yağlama yetersizliği nedeniyle bilye yüzeylerinde mikron düzeyinde aşınma oluşmuştur.",
        "corrective_actions": "1. Spindle rulmanı seramik rulman ile değiştirildi.\n2. Otomatik yağlama ünitesi debi ayarı artırıldı.",
        "lessons_learned": "Titreşim analizi sensörleri CNC tezgahına entegre edilerek kestirimci bakım sistemine veri aktarımı sağlandı.",
        "severity": 7, "occurrence": 4, "detection": 3,
        "task_title": "Spindle seramik rulman montajı ve yağlama ayarı",
        "task_status": "in_progress",
        "assignee": "Ali Öztürk (Üretim Sorumlusu)"
    },
    {
        "department": "Üretim",
        "title": "Montaj Hattında Robotik Kol Pozisyonlama Sapması ve Duraksama",
        "description": "6 eksenli montaj robotu gövde birleştirme aşamasında 1.5mm sapma yaparak koruma bariyerlerini tetikledi ve hattı durdurdu.",
        "methodology": "fishbone",
        "category": "Otomasyon & Robotik",
        "industry": "Elektronik Montaj",
        "root_cause": "Eksen enkoder kablosundaki kırılma ve servomotor sürücüsündeki voltaj dalgalanması koordinat sapmasına neden olmuştur.",
        "corrective_actions": "1. Enkoder kablo demeti esnek eskay kablo ile yenilendi.\n2. Servo sürücüye kesintisiz güç kaynağı eklendi.",
        "lessons_learned": "Robotik kol esnek kablolarının flex ömrü takibi için döngü sayacı yazılımı devreye alındı.",
        "severity": 9, "occurrence": 3, "detection": 2,
        "task_title": "Robot kablo demeti değişimi ve enkoder sıfırlama",
        "task_status": "on_hold",
        "proof_description": "Robot üreticisi Almanya teknik ekibinden parametre onay dosyası bekleniyor.",
        "assignee": "Kadir Şen (Montaj Şefi)"
    },
    {
        "department": "Üretim",
        "title": "Pres Makinesinde Hidrolik Yağ Sıcaklığı Artışı ve Basınç Kaybı",
        "description": "250 tonluk eksantrik pres makinesinde hidrolik yağ sıcaklığı 78°C seviyesine ulaştı. Pres basma hızı %30 yavaşladı.",
        "methodology": "a3",
        "category": "Hidrolik & Pres",
        "industry": "Metal Şekillendirme",
        "root_cause": "Yağ soğutma radyatörünün toz kirliliği nedeniyle tıkanması ve soğutma fanı motor rölesinin yapışması.",
        "corrective_actions": "1. Eşanjör radyatörü kimyasal yıkama ile temizlendi.\n2. Fan motor rölesi katı hal (SSR) röle ile değiştirildi.",
        "lessons_learned": "Hidrolik yağ eşanjör filtre temizliği haftalık otonom bakım checklist'ine eklendi.",
        "severity": 6, "occurrence": 6, "detection": 3,
        "task_title": "Eşanjör kimyasal temizliği ve SSR röle değişimi",
        "task_status": "completed",
        "assignee": "Hasan Kaya (Bakım Şefi)"
    },
    {
        "department": "Üretim",
        "title": "Konveyör Bant Motorunda Aşırı Isınma ve Rulman Kilitlenmesi",
        "description": "Hat 2 ana konveyör bant motoru aşırı akım çekerek termik şalteri attırdı. Motor gövde sıcaklığı 92°C ölçüldü.",
        "methodology": "fmea",
        "category": "Mekanik Bakım",
        "industry": "Gıda Paketleme",
        "root_cause": "Motor ön kapağındaki toz keçesinin yırtılması sonucu un tozunun rulman gresine karışması ve gresi kurutması.",
        "corrective_actions": "1. Motor rulmanları ve keçe takımı yenilendi.\n2. Motor arka kısmına koruyucu paslanmaz siperlik takıldı.",
        "lessons_learned": "Tozlu ortamlarda çalışan elektrik motorları IP66 koruma sınıfı motorlar ile kademeli olarak revize edilecek.",
        "severity": 7, "occurrence": 5, "detection": 4,
        "task_title": "IP66 motor temini ve konveyör motor değişimi",
        "task_status": "todo",
        "assignee": "Mehmet Can (Bakım Mühendisi)"
    },
    {
        "department": "Üretim",
        "title": "Otomatik Paketleme Hattında Sensör Kirlenmesi ve Hatalı Duruş",
        "description": "Paketleme hattındaki fotosel sensörlerin toz kaplaması nedeniyle boş paket algılandı uyarısı vererek hattı saatte 12 kez durdurması.",
        "methodology": "5why",
        "category": "Sensör & Algılama",
        "industry": "Hızlı Tüketim",
        "root_cause": "Ürün koli dolum kısmında püskürtme memesinden kaçan toz partiküllerinin hava akımı ile sensör camına yapışması.",
        "corrective_actions": "1. Sensör önüne otomatik hava üfleme (air purge) aparatı takıldı.\n2. Toz emiş nozülünün pozisyonu optimize edildi.",
        "lessons_learned": "Optik sensörlerde hava üfleme aparatları standart kurulum ekipmanı haline getirildi.",
        "severity": 5, "occurrence": 8, "detection": 2,
        "task_title": "Air purge hava üfleme aparatı montajı",
        "task_status": "completed",
        "assignee": "Ali Öztürk (Üretim Sorumlusu)"
    },
    {
        "department": "Üretim",
        "title": "Alüminyum Döküm Ocağında Derece Sıcaklığı Dalgalanması",
        "description": "Ergitme ocağında erimiş alüminyum sıcaklığı ±35°C dalgalanarak döküm parçalarında gaz boşluğu hatasına yol açtı.",
        "methodology": "8d",
        "category": "Termal İşlem",
        "industry": "Döküm Sanayi",
        "root_cause": "Termokupl koruma kılıfının cüruf birikmesiyle ısı iletimini geciktirmesi ve PID kontrolör parametrelerinin bozulması.",
        "corrective_actions": "1. SiC koruma kılıflı yeni termokupl takıldı.\n2. PID ototune işlemi yapılıp ısıtıcı rezistans grubu dengelendi.",
        "lessons_learned": "Döküm sıcaklık ölçüm kalibrasyonları her vardiya başında dijital el termometresi ile doğrulanacak.",
        "severity": 8, "occurrence": 4, "detection": 3,
        "task_title": "SiC koruma kılıflı termokupl değişimi ve PID tuning",
        "task_status": "in_progress",
        "assignee": "Kadir Şen (Montaj Şefi)"
    },
    {
        "department": "Üretim",
        "title": "Lazer Kesim Makinesinde Odaklama Lensi Çizilmesi ve Çapaklı Kesim",
        "description": "Fiber lazer kesim makinesinde 4mm paslanmaz sac kesimlerinde alt kenarlarda çapak birikti ve kesim hızı %40 düştü.",
        "methodology": "fishbone",
        "category": "Lazer & Optik",
        "industry": "Sac İşleme",
        "root_cause": "Koruyucu camın delinmesi sonucu kesim kafasına sıçrayan çapakların koruyucu lens üzerine yapışıp merceği çizmesi.",
        "corrective_actions": "1. Odaklama lensi ve koruyucu cam yenilendi.\n2. Azot gazı nozül basıncı 14 bar'dan 18 bar'a yükseltildi.",
        "lessons_learned": "Koruyucu cam kirlilik sensörü alarmı kontrol paneline entegre edilerek erken uyarı sağlandı.",
        "severity": 7, "occurrence": 5, "detection": 2,
        "task_title": "Fiber lazer optik mercek değişimi ve azot basınç testi",
        "task_status": "completed",
        "assignee": "Hasan Kaya (Bakım Şefi)"
    },
    {
        "department": "Üretim",
        "title": "Otomotiv Gövde Kaynak İstasyonunda Çapak Birikmesi ve Kaynak Atması",
        "description": "Punta kaynak robotunun bakır elektrot uçlarında çapak birikmesi sonucu Punta kaynak birleşme mukavemeti 4.2 kN'a düştü.",
        "methodology": "a3",
        "category": "Kaynak & Birleştirme",
        "industry": "Otomotiv",
        "root_cause": "Elektrot bileme (tip dresser) bıçaklarının körelmesi ve kaynak akım süresinin aşırı ısınmaya yol açması.",
        "corrective_actions": "1. Tip dresser elmas bıçakları değiştirildi.\n2. Otomatik elektrot bileme periyodu 250 puntadan 150 puntaya düşürüldü.",
        "lessons_learned": "Punta kaynak kalitesi tahribatsız ultrasonik kaynak kontrol cihazı ile 2 saatte bir denetlenecek.",
        "severity": 9, "occurrence": 3, "detection": 3,
        "task_title": "Kaynak tip dresser bıçak değişimi ve oto-bileme ayarı",
        "task_status": "todo",
        "assignee": "Mehmet Can (Bakım Mühendisi)"
    },
    {
        "department": "Üretim",
        "title": "Sıcak Haddeleme Hattında Merdane Aşınması ve Kalınlık Toleransı Sapması",
        "description": "Haddeleme hattından çıkan şerit çelik kalınlığı 3.0mm yerine 3.25mm ölçülerek müşteri standartlarının dışına çıktı.",
        "methodology": "fmea",
        "category": "Metal Haddeleme",
        "industry": "Demir Çelik",
        "root_cause": "Hadde merdane yüzeyinde termal yorulmaya bağlı mikron düzeyinde aşınma oluğu oluşması.",
        "corrective_actions": "1. Hadde merdane takımı rektifiye edilmek üzere taşlama atölyesine gönderildi.\n2. Yedek merdane seti takılarak hat sıfırlandı.",
        "lessons_learned": "Merdane çalışma tonajı takibi otomatik olarak yapılıp 5000 tonda bir taşlama programına alınacak.",
        "severity": 8, "occurrence": 4, "detection": 2,
        "task_title": "Yedek hadde merdane seti montajı ve kalınlık kalibrasyonu",
        "task_status": "in_progress",
        "assignee": "Ali Öztürk (Üretim Sorumlusu)"
    },

    # --- LOJİSTİK (10 Scenarios) ---
    {
        "department": "Lojistik",
        "title": "Depo Otomasyon Sisteminde Barkod Okuyucu Çakışması ve Yanlış Adresleme",
        "description": "Otomatik toplama konveyöründe el terminalleri ve sabit barkod okuyucuların IP çakışması yapması sonucu paletler yanlış adres raflarına yönlendirildi.",
        "methodology": "5why",
        "category": "WMS & Depo",
        "industry": "Perakende Lojistik",
        "root_cause": "DHCP sunucusundaki statik IP aralığı tanımlamasının el terminali güncellemesinde çakışması.",
        "corrective_actions": "1. Tüm sabit okuyuculara statik IP atandı.\n2. WMS yönlendirme algoritması çift doğrulama kuralı ile güncellendi.",
        "lessons_learned": "Lojistik donanımlarında IP adresi havuzu ağ yönetimi dokümanına bağlandı.",
        "severity": 7, "occurrence": 4, "detection": 3,
        "task_title": "Barkod okuyucu statik IP yapılandırması ve WMS kuralı",
        "task_status": "completed",
        "assignee": "Fatma Şahin (Tesis Sorumlusu)"
    },
    {
        "department": "Lojistik",
        "title": "Soğuk Hava Deposu Kapı Kontrol Sensörü Arızası ve Isı Yükselmesi",
        "description": "-18°C dondurulmuş gıda deposu hızlı sarmal kapısının açık kalması sonucu depo içi sıcaklık -11°C seviyesine yükseldi.",
        "methodology": "8d",
        "category": "Soğuk Zincir",
        "industry": "Gıda Lojistiği",
        "root_cause": "Hızlı kapı emniyet fotoselinin alt kısmındaki karlanma nedeniyle kapının kapanma komutunu iptal etmesi.",
        "corrective_actions": "1. Fotosel camlarına rezistanslı ısıtıcı çerçeve takıldı.\n2. Kapı 45 saniyeden fazla açık kaldığında çalan yüksek sesli siren eklendi.",
        "lessons_learned": "Soğuk depo kapılarında ısıtıcılı emniyet sensörü standardı getirildi.",
        "severity": 9, "occurrence": 3, "detection": 2,
        "task_title": "Isıtıcılı sensör çerçeve montajı ve alarm entegrasyonu",
        "task_status": "completed",
        "assignee": "Caner Kaya (Operasyon Direktörü)"
    },
    {
        "department": "Lojistik",
        "title": "Mal Kabul Rampasında Forklift Trafik Sıkışıklığı ve Sevkiyat Gecikmesi",
        "description": "Saat 14:00-16:00 arası 8 tırın aynı anda gelmesiyle mal kabul rampasında 2 saatlik araç bekleme kuyruğu oluştu.",
        "methodology": "fishbone",
        "category": "Saha Operasyonu",
        "industry": "Dağıtım Merkezi",
        "root_cause": "Tedarikçi slot randevu sisteminin entegre çalışmaması ve rampalardan 2 tanesinin arızalı yük platformu nedeniyle kapatılması.",
        "corrective_actions": "1. Rampalardaki yük platformu hidrolik pistonları tamir edildi.\n2. Tedarikçi randevu portalı zorunlu hale getirildi.",
        "lessons_learned": "Tedarikçi tır gelişleri 30 dakikalık slotlara bölünerek rampa yükü dengelendi.",
        "severity": 6, "occurrence": 6, "detection": 2,
        "task_title": "Rampa hidrolik platform tamiri ve slot randevu sistemi",
        "task_status": "in_progress",
        "assignee": "Volkan Aydoğan (Depo Şefi)"
    },
    {
        "department": "Lojistik",
        "title": "Yurtdışı Konteyner Yüklemesinde Palet Ölçü Uyumsuzluğu ve Hacim Kaybı",
        "description": "Almanya sevkiyatında 40'lık High Cube konteynere paletlerin taşma yapması sebebiyle 24 palet yerine 20 palet yüklenebildi.",
        "methodology": "a3",
        "category": "Sevkiyat & Paketleme",
        "industry": "Uluslararası Taşımacılık",
        "root_cause": "Paketleme streçleme makinesinin palet kenarlarından 4'er cm taşma yapacak şekilde ayarsız sarım yapması.",
        "corrective_actions": "1. Otomatik streç sarma makinesi ön germe ve kenar baskı ayarları kalibre edildi.\n2. Palet kontrol mastarı imal edildi.",
        "lessons_learned": "Konteyner yükleme öncesi palet en-boy ölçümü lazer ölçüm şeridi ile kontrol edilecek.",
        "severity": 7, "occurrence": 4, "detection": 3,
        "task_title": "Streç sarma makinesi kalibrasyonu ve palet mastar imali",
        "task_status": "completed",
        "assignee": "Fatma Şahin (Tesis Sorumlusu)"
    },
    {
        "department": "Lojistik",
        "title": "Otonom Yönlendirmeli Araç (AGV) Batarya Hızlı Düşüşü ve Hat Durması",
        "description": "Depo içi parça taşıyan AGV-03 aracının şarjı 4 saatte tükenerek ana koridorda durması ve malzeme akışını kesmesi.",
        "methodology": "fmea",
        "category": "AGV & Robotik",
        "industry": "Akıllı Depolama",
        "root_cause": "LiFePO4 batarya paketindeki 3. hücrenin voltaj çökmesi yaşaması ve BMS kartının erken kesme yapması.",
        "corrective_actions": "1. AGV-03 batarya paketi yeni nesil hızlı şarjlı paket ile değiştirildi.\n2. Otomatik fırsat şarj (opportunity charging) istasyonu sayısı artırıldı.",
        "lessons_learned": "AGV batarya sağlık durumları (SoH) WMS paneline canlı telemetri ile bağlandı.",
        "severity": 8, "occurrence": 3, "detection": 3,
        "task_title": "AGV batarya değişimi ve fırsat şarj istasyonu kurulumu",
        "task_status": "on_hold",
        "proof_description": "İthal LiFePO4 batarya modülünün gümrük çekim işlemleri sürüyor.",
        "assignee": "Caner Kaya (Operasyon Direktörü)"
    },
    {
        "department": "Lojistik",
        "title": "Konveyör Ayırma (Sorter) İstasyonunda Hatalı Yönlendirme ve Ürün Karışması",
        "description": "E-ticaret sipariş ayrıştırma sorter cihazının koli ağırlık sensörünün sıfırlanmaması nedeniyle B bölgesindeki ürünlerin C bölgesine atılması.",
        "methodology": "5why",
        "category": "Otomasyon & Sorter",
        "industry": "E-Ticaret Lojistiği",
        "root_cause": "Dinamik tartı konveyörünün altına sıkışan ambalaj atığının tartım hücresine (loadcell) mekanik baskı yapması.",
        "corrective_actions": "1. Tartım hücresi altı körüklü koruma muhafazası ile kapatıldı.\n2. Otomatik dara alma sıfırlama yazılım döngüsü eklendi.",
        "lessons_learned": "Tartı konveyörleri her vardiya değişiminde 1kg standart ağırlık ile kontrol edilecek.",
        "severity": 7, "occurrence": 5, "detection": 2,
        "task_title": "Loadcell koruma körüğü montajı ve dara sıfırlama yazılımı",
        "task_status": "completed",
        "assignee": "Volkan Aydoğan (Depo Şefi)"
    },
    {
        "department": "Lojistik",
        "title": "Tedarikçi Koli Ambalaj Dayanıksızlığı ve Hasarlı Mal Teslimatı",
        "description": "Bursa tedarikçisinden gelen 150 koli yedek parçanın alt kolilerinin ezilmesi sonucu 18 adet ürünün hasar görmesi.",
        "methodology": "8d",
        "category": "Tedarik Zinciri",
        "industry": "Otomotiv Lojistiği",
        "root_cause": "Tedarikçinin maliyet düşürmek için oluklu mukavva kalitesini Dopel (B+C) katmandan tek dalga katmana düşürmesi.",
        "corrective_actions": "1. Tedarikçiye uygunsuzluk bülteni bildirilip hasarlı ürün maliyeti rücu edildi.\n2. Koli mukavemet şartnamesi ECT 32 standardına çekildi.",
        "lessons_learned": "Mal kabulde koli ezilme direnci (BCT) numune kontrolü zorunlu hale getirildi.",
        "severity": 6, "occurrence": 5, "detection": 4,
        "task_title": "Tedarikçi ambalaj spesifikasyon revizyonu ve kabul denetimi",
        "task_status": "in_progress",
        "assignee": "Fatma Şahin (Tesis Sorumlusu)"
    },
    {
        "department": "Lojistik",
        "title": "WMS Depo Yönetim Yazılımında Stok Senkronizasyon Gecikmesi",
        "description": "Sistemde var görünen 45 adet ürünün rafta bulunamaması sebebiyle müşteri siparişlerinin %12'sinin eksik sevk edilmesi.",
        "methodology": "fishbone",
        "category": "WMS Yazılımı",
        "industry": "Depo Yönetimi",
        "root_cause": "El terminali offline mod geçişlerinde veri tabanı senkronizasyon servisinin kilitlenmesi ve kayıp paketler.",
        "corrective_actions": "1. WMS sync servisi WebSocket mimarisi ile yeniden yazıldı.\n2. Çift yönlü transactional mesaj kuyruğu aktif edildi.",
        "lessons_learned": "Stok hareketlerinde anlık lokasyon düşümü olmadan sipariş toplama emri oluşturulmayacak.",
        "severity": 8, "occurrence": 4, "detection": 3,
        "task_title": "WMS WebSocket sync servisi güncellemesi",
        "task_status": "completed",
        "assignee": "Caner Kaya (Operasyon Direktörü)"
    },
    {
        "department": "Lojistik",
        "title": "Gümrük Evrak Hazırlama Sürecinde GTİP Kodu Hataları ve Gecikme",
        "description": "İtalya'ya ihraç edilen hidrolik valf grubunun GTİP kodunun beyannamede yanlış yazılması sebebiyle konteynerin gümrükte 4 gün beklemesi.",
        "methodology": "a3",
        "category": "Gümrük & Mevzuat",
        "industry": "Dış Ticaret",
        "root_cause": "Ürün kütüphanesindeki teknik tanım değişikliğinin gümrük müşavirliği portalına otomatik aktarılmaması.",
        "corrective_actions": "1. ERP ve Gümrük Müşaviri yazılımı arasında GTİP doğrulama API entegrasyonu sağlandı.\n2. Gümrük cezası tedarikçi sigortasından karşılandı.",
        "lessons_learned": "Yeni ürün tanımında GTİP kodu onay mekanizması Hukuk & Mevzuat birimine bağlandı.",
        "severity": 7, "occurrence": 3, "detection": 4,
        "task_title": "ERP-Gümrük Müşaviri API entegrasyonu kurulumu",
        "task_status": "todo",
        "assignee": "Volkan Aydoğan (Depo Şefi)"
    },
    {
        "department": "Lojistik",
        "title": "Filo Araçlarında GPS Takip Modülü İletişim Kopukluğu ve Rota Sapması",
        "description": "Dağıtım yapan 6 kamyonun GPS modüllerinin dağlık güzergahta sinyal kesintisi yaşaması sonucu müşteri teslimat zamanlarının izlenememesi.",
        "methodology": "fmea",
        "category": "Filo Yönetimi",
        "industry": "Şehir İçi Dağıtım",
        "root_cause": "Tek operatörlü SIM kartların kapsama alanı dışına çıkması ve cihaz dahili hafızasının küçük olması.",
        "corrective_actions": "1. GPS cihazları çift SIM kartlı (M2M roaming) modüller ile değiştirildi.\n2. Offline konum kaydetme bellek kapasitesi 128MB'a çıkarıldı.",
        "lessons_learned": "Filo araçlarında küresel dolaşımlı M2M veri hatları standart haline getirildi.",
        "severity": 6, "occurrence": 5, "detection": 2,
        "task_title": "Çift SIM kartlı M2M GPS cihaz değişimi",
        "task_status": "in_progress",
        "assignee": "Fatma Şahin (Tesis Sorumlusu)"
    },

    # --- KALİTE (10 Scenarios) ---
    {
        "department": "Kalite",
        "title": "Enjeksiyon Parçalarda İç Gerilmeye Bağlı Çatlama ve Deformasyon",
        "description": "Şeffaf polikarbonat kapak parçalarında montaj sonrası 24 saat içinde kılcal çatlaklar (crazing) oluştuğu tespit edildi.",
        "methodology": "5why",
        "category": "Malzeme Hatası",
        "industry": "Medikal Cihaz",
        "root_cause": "Hammadde kurutma sıcaklığının 120°C yerine 95°C yapılmasından dolayı nem oranının %0.02 yerine %0.08 kalması.",
        "corrective_actions": "1. Hammadde kurutucu desikant filtreleri yenilendi.\n2. Kurutucuya otomatik çiğ noktası (dew-point) sensörü takıldı.",
        "lessons_learned": "Polikarbonat hammaddelerde nem ölçümü yapılmadan enjeksiyon kovanına besleme yapılmayacak.",
        "severity": 9, "occurrence": 3, "detection": 3,
        "task_title": "Dew-point nem sensörü montajı ve desikant değişimi",
        "task_status": "completed",
        "assignee": "Ahmet Yılmaz (Kalite Uzmanı)"
    },
    {
        "department": "Kalite",
        "title": "Kaplama Hattında Banyo Ph Değeri Sapması ve Korozyon Direnci Düşüklüğü",
        "description": "Çinko-Nikel kaplama yapılan cıvataların tuz testi dayanımının 1000 saat yerine 450 saatte beyaz pas vermesi.",
        "methodology": "8d",
        "category": "Yüzey İşlem",
        "industry": "Kalıp & Bağlantı Elemanları",
        "root_cause": "Banyo pH probunun kirlenerek pH değerini 0.8 birim hatalı yüksek ölçmesi ve asit dozajının eksik yapılması.",
        "corrective_actions": "1. pH propları cam elektrotlu otomatik yıkayıcılı model ile değiştirildi.\n2. Günlük standart tampon çözelti kalibrasyonu kuralı kondu.",
        "lessons_learned": "Tüm kaplama banyoları için haftalık tuz püskürtme korozyon testi şahit numuneleri saklanacak.",
        "severity": 8, "occurrence": 4, "detection": 2,
        "task_title": "Otomatik yıkayıcılı pH probu montajı ve tuz testi",
        "task_status": "in_progress",
        "assignee": "Merve Şahin (Kalite Mühendisi)"
    },
    {
        "department": "Kalite",
        "title": "Tahribatsız Muayene (NDT) Ultrasonik Testinde Sahte Hata Sinyalleri",
        "description": "Dövme çelik şaftların ultrasonik çatlak testinde sağlam parçaların %15'inin hatalı olarak hurdaya ayrılması.",
        "methodology": "fishbone",
        "category": "NDT Testi",
        "industry": "Ağır Sanayi",
        "root_cause": "Jel temas maddesinin (couplant) içinde hava kabarcığı kalması ve prob kristal yüzeyindeki çizik.",
        "corrective_actions": "1. Otomatik jel püskürtme ve vakumlu kabarcık alma ünitesi eklendi.\n2. Ultrasonik prob kafası yenilendi.",
        "lessons_learned": "NDT test operatörleri Seviye 2 (Level II) sertifikasyon eğitimi tazeleme programına alındı.",
        "severity": 7, "occurrence": 5, "detection": 2,
        "task_title": "Vakumlu jel ünitesi montajı ve NDT prob değişimi",
        "task_status": "on_hold",
        "proof_description": "NDT Level II sertifikalı dış denetçinin eğitim takvimi bekleniyor.",
        "assignee": "Mehmet Demir (Üretim Müdürü)"
    },
    {
        "department": "Kalite",
        "title": "Tedarikçi Hammadde Sertlik Derecesi Tolerans Dışı Gelişi",
        "description": "Gelen 4140 ıslah çeliği millerinin sertliğinin 28 HRC yerine 38 HRC gelmesi sonucu işleme kalıplarının kırılması.",
        "methodology": "a3",
        "category": "Giriş Kalite",
        "industry": "Savunma Sanayi",
        "root_cause": "Tedarikçinin tavlama fırını soğutma fanı arızası nedeniyle malzemeyi hızlı soğutarak martenzit yapı oluşturması.",
        "corrective_actions": "1. Parti karantinaya alınıp tedarikçiye iade edildi.\n2. Giriş kalitede 3D spektrometre ve sertlik ölçüm numune sayısı 2 katına çıkarıldı.",
        "lessons_learned": "Kritik çelik girdilerinde tedarikçiden fırın sıcaklık grafiği (coil sertifikası) zorunlu kılındı.",
        "severity": 9, "occurrence": 3, "detection": 3,
        "task_title": "Tedarikçi iade işlemleri ve giriş kalite denetim sıklaştırma",
        "task_status": "completed",
        "assignee": "Ahmet Yılmaz (Kalite Uzmanı)"
    },
    {
        "department": "Kalite",
        "title": "CMM Ölçüm Cihazı Kalibrasyon Kayması ve Hatalı Ölçüm Raporları",
        "description": "3 boyutlu CMM ölçüm cihazının Z ekseninde 8 mikron sapma yaparak doğru parçaları red olarak raporlaması.",
        "methodology": "fmea",
        "category": "Ölçüm & Kalibrasyon",
        "industry": "Havacılık",
        "root_cause": "Ölçüm laboratuvarı klima iklimlendirmesinin gece kapanması sonucu oda sıcaklığının 20°C'den 28°C'ye yükselip granit tablayı genleştirmesi.",
        "corrective_actions": "1. Ölçüm laboratuvarına 7/24 hassas ±0.5°C iklimlendirme kliması takıldı.\n2. CMM yakut bilye prob kalibrasyonu seramik küre ile tazelendi.",
        "lessons_learned": "Ölçüm laboratuvarı sıcaklık ve nem değerleri IoT sensör ile 15 dakikada bir veri tabanına kaydedilecek.",
        "severity": 8, "occurrence": 4, "detection": 2,
        "task_title": "Hassas laboratuvar kliması montajı ve CMM kalibrasyonu",
        "task_status": "completed",
        "assignee": "Merve Şahin (Kalite Mühendisi)"
    },
    {
        "department": "Kalite",
        "title": "Ürün Ambalaj Sızdırmazlık Testinde Basınç Düşüşü ve Hava Kaçağı",
        "description": "Steril medikal poşet ambalajlarının yapıştırma dikiş hattında 0.3 bar basınçta hava kaçağı tespit edilmesi.",
        "methodology": "5why",
        "category": "Ambalaj Kalite",
        "industry": "Medikal",
        "root_cause": "Sıcak çene yapıştırma rezistansının sol tarafında Teflon bant aşınması nedeniyle ısı iletiminin düşmesi.",
        "corrective_actions": "1. Yapıştırma çenesi Teflon kaplaması yenilendi.\n2. Çene sıcaklık dağılımı termal kamera ile doğrulandı.",
        "lessons_learned": "Ambalaj yapıştırma çene teflonları her 10.000 baskıda bir periyodik olarak değiştirilecek.",
        "severity": 9, "occurrence": 3, "detection": 2,
        "task_title": "Rezistans teflon bant değişimi ve termal kamera kontrolü",
        "task_status": "completed",
        "assignee": "Mehmet Demir (Üretim Müdürü)"
    },
    {
        "department": "Kalite",
        "title": "Boya İstasyonunda Nem Oranı Artışına Bağlı Portakallanma Hatası",
        "description": "Beyaz eşya dış panel elektrostatik toz boya uygulamasında yüzeyde pürüzlü portakallanma görüntüsü oluşması.",
        "methodology": "8d",
        "category": "Yüzey Kalite",
        "industry": "Beyaz Eşya",
        "root_cause": "Kompresör hattı kurutucusunun arızalanması sonucu toz boya tabancasına nemli hava gitmesi.",
        "corrective_actions": "1. Hava hattına aktif karbonlu desikant hava kurutucu eklendi.\n2. Boya kabin nem oranı %45 seviyesine sabitlendi.",
        "lessons_learned": "Pnömatik boya hatlarına su tutucu otomatik tahliye valfleri monte edildi.",
        "severity": 6, "occurrence": 6, "detection": 2,
        "task_title": "Desikant hava kurutucu montajı ve nem kontrolü",
        "task_status": "in_progress",
        "assignee": "Ahmet Yılmaz (Kalite Uzmanı)"
    },
    {
        "department": "Kalite",
        "title": "Ultrasonik Kaynaklı Plastik Birleşim yerlerinde Kopma Kuvveti Yetersizliği",
        "description": "Araç stop lambası şeffaf cam birleşim yerinin çekme testinde 350N olan standart altında 210N'da ayrılması.",
        "methodology": "fishbone",
        "category": "Plastik Birleştirme",
        "industry": "Otomotiv Aydınlatma",
        "root_cause": "Ultrasonik kaynak sonotrodunun frekans kayması yapması (19.8 kHz) ve kaynak genliğinin düşük kalması.",
        "corrective_actions": "1. Sonotrod titanyum kafa jeneratör ile yeniden akort (tune) edildi.\n2. Kaynak kaynağı öncesi enerji moduna geçildi.",
        "lessons_learned": "Ultrasonik kaynak makinelerinde zaman modu yerine joule cinsinden enerji modu standartlaştırıldı.",
        "severity": 8, "occurrence": 4, "detection": 3,
        "task_title": "Sonotrod frekans akort işlemi ve enerji modu aktivasyonu",
        "task_status": "todo",
        "assignee": "Merve Şahin (Kalite Mühendisi)"
    },
    {
        "department": "Kalite",
        "title": "Final Kontrol Aşamasında Görsel Etiket Uyumsuzluğu ve Müşteri Şikayeti",
        "description": "Müşteriye gönderilen 50 kolide ürün etiketindeki seri numarasının koli içindeki ürünle eşleşmemesi hatası.",
        "methodology": "a3",
        "category": "Etiketleme & İzlenebilirlik",
        "industry": "Elektronik",
        "root_cause": "Paketleme operatörünün yazıcı çıktısını alırken bir önceki partinin etiket rulosunu değiştirmeyi unutması.",
        "corrective_actions": "1. Konveyör sonuna kameralı etiket okuma doğrulama (Vision System) entegre edildi.\n2. Eşleşmeyen etiketlerde konveyör otomatik durdurmaya bağlandı.",
        "lessons_learned": "Etiket basımında manuel müdahale kaldırılıp ERP iş emri barkodu okutularak otomatik basıma geçildi.",
        "severity": 7, "occurrence": 4, "detection": 4,
        "task_title": "Kameralı etiket doğrulama vision sistemi kurulumu",
        "task_status": "completed",
        "assignee": "Mehmet Demir (Üretim Müdürü)"
    },
    {
        "department": "Kalite",
        "title": "Statik Elektrik Birikmesine Bağlı Hassas Elektronik Kart Hasarı",
        "description": "SMD montaj hattından çıkan kontrol kartlarının %3'ünün işlevsel testte (FCT) mikroişlemci arızası vermesi.",
        "methodology": "fmea",
        "category": "ESD & Elektronik",
        "industry": "Elektronik İmalat",
        "root_cause": "ESD bileklik topraklama hattındaki kopukluk ve alan zemin iyonizerlerinin performans düşüklüğü.",
        "corrective_actions": "1. ESD zemin kaplaması bakır şeritler ile yeniden topraklandı.\n2. Sürekli bileklik doğrulama monitörleri çalışma tezgahlarına takıldı.",
        "lessons_learned": "ESD korumalı alanlara giriş turnikesi bileklik ve ayakkabı direnç test cihazına bağlandı.",
        "severity": 9, "occurrence": 3, "detection": 4,
        "task_title": "ESD topraklama hattı yenileme ve tezgah monitörleri",
        "task_status": "in_progress",
        "assignee": "Ahmet Yılmaz (Kalite Uzmanı)"
    },

    # --- BİLGİ İŞLEM (10 Scenarios) ---
    {
        "department": "Bilgi İşlem",
        "title": "Mikroservis API Yanıt Süresinde 450ms Gecikme ve Veritabanı Darboğazı",
        "description": "Sipariş mikroservisinde ortalama HTTP yanıt süresi 80ms seviyesinden 450ms seviyesine yükseldi. CPU kullanımı %90'a ulaştı.",
        "methodology": "5why",
        "category": "Yazılım Performansı",
        "industry": "Yazılım & Bilişim",
        "root_cause": "N+1 SQL sorgusu problemi ve indeks eksikliği sebebiyle sorguların full table scan yapması.",
        "corrective_actions": "1. OrderItem ilişkisinde eger loading (selectinload) uygulandı.\n2. user_id ve status kolonlarına bileşik (composite) B-Tree indeksi eklendi.",
        "lessons_learned": "ORM sorgularında SQL profil akışı CI/CD aşamasında otomatik sorgu analiz aracı ile denetlenecek.",
        "severity": 8, "occurrence": 5, "detection": 2,
        "task_title": "Composite B-Tree indeks eklenmesi ve ORM sorgu optimizasyonu",
        "task_status": "completed",
        "assignee": "Burak Öz (Kıdemli Backend Geliştirici)"
    },
    {
        "department": "Bilgi İşlem",
        "title": "PostgreSQL Bağlantı Havuzu (Connection Pool) Tıkanması ve 504 Gateway Timeout",
        "description": "Yoğun trafik anında veritabanı bağlantı sayısı maksimum sınır olan 100'e ulaştı ve yeni istekler yanıt alamayarak zaman aşımına uğradı.",
        "methodology": "8d",
        "category": "Veritabanı & Altyapı",
        "industry": "Bulut Servisleri",
        "root_cause": "Asyncio havuzunda kapanmayan sızıntı (unclosed session) bağlantıları ve PgBouncer bağlantı limitleme ayarsızlığı.",
        "corrective_actions": "1. PgBouncer transaction mode ayarı ile veritabanı önüne koyuldu.\n2. SQLAlchemy context manager try-finally blokları ile sağlamlaştırıldı.",
        "lessons_learned": "Async veritabanı bağlantılarında pool_pre_ping ve max_overflow parametreleri optimize edildi.",
        "severity": 9, "occurrence": 4, "detection": 2,
        "task_title": "PgBouncer kurulumu ve SQLAlchemy pool ayarları",
        "task_status": "completed",
        "assignee": "Selin Arslan (Software Lead)"
    },
    {
        "department": "Bilgi İşlem",
        "title": "Redis Cache Sunucusunda Bellek Taşması ve Yanıt Sürelerinde Yükselme",
        "description": "Önbellek sunucusu 8GB RAM sınırına ulaşarak maxmemory eviction politikasını tetikledi ve ana sayfada 2 sn gecikmeye neden oldu.",
        "methodology": "fishbone",
        "category": "Cache & Performans",
        "industry": "E-Ticaret Altyapısı",
        "root_cause": "Oturum verilerine TTL (Time-To-Live) süresi atanmaması ve noeviction modunda bellek dolması.",
        "corrective_actions": "1. Eviction politikası volatile-lru olarak değiştirildi.\n2. Tüm kilit nesnelerine varsayılan 3600 sn TTL eklendi.",
        "lessons_learned": "Redis bellek kullanımı Prometheus & Grafana alarmları ile %80 seviyesinde uyarı verecek şekilde yapılandırıldı.",
        "severity": 7, "occurrence": 5, "detection": 2,
        "task_title": "Redis volatile-lru konfigürasyonu ve TTL eklenmesi",
        "task_status": "in_progress",
        "assignee": "Ahmet Yılmaz (Kıdemli Bulut Mimar)"
    },
    {
        "department": "Bilgi İşlem",
        "title": "Kubernetes Kümesinde Pod CrashLoopBackOff Hatası ve Oto-Ölçekleme Başarısızlığı",
        "description": "Production Kubernetes kümesinde ödeme servisi podları OOMKilled (Out of Memory) hatası alarak sürekli yeniden başladı.",
        "methodology": "a3",
        "category": "DevOps & Kubernetes",
        "industry": "Fintek",
        "root_cause": "Pod memory limit değerinin (256Mi) uygulama JVM heap ihtiyacının (512Mi) altında tanımlanması.",
        "corrective_actions": "1. Pod memory request 512Mi, limit 1Gi seviyesine çıkarıldı.\n2. HPA (Horizontal Pod Autoscaler) CPU & Memory %70 eşiğine ayarlandı.",
        "lessons_learned": "Tüm mikroservisler için yük testi yapılarak kaynak limitleri gerçekçi değerler ile belirlenecek.",
        "severity": 9, "occurrence": 3, "detection": 3,
        "task_title": "Kubernetes deployment YAML memory limit revizyonu",
        "task_status": "completed",
        "assignee": "Deniz Er (IT Ops Manager)"
    },
    {
        "department": "Bilgi İşlem",
        "title": "CI/CD Deployment Boru Hattında Docker Image Yapılandırma Hatası",
        "description": "GitLab CI boru hattında production ortamına yapılan dağıtımın 'base image not found' hatası vererek derlemeyi durdurması.",
        "methodology": "fmea",
        "category": "CI/CD & Otomasyon",
        "industry": "Yazılım Evi",
        "root_cause": "Docker Hub üzerindeki node:18-alpine etiketli majör imajın güncellenmesi ve uyumsuz bağımlılık yaratması.",
        "corrective_actions": "1. Dockerfile imaj etiketleri hash (sha256) digest ile sabitleştirildi.\n2. Özel Nexus Docker registry kurulumu tamamlandı.",
        "lessons_learned": "CI/CD derlemelerinde dış imaj bağımlılığı kaldırılıp yerel güvenli artifact depoları kullanılacak.",
        "severity": 6, "occurrence": 6, "detection": 2,
        "task_title": "Nexus Docker registry kurulumu ve SHA digest sabitleme",
        "task_status": "todo",
        "assignee": "Burak Öz (Kıdemli Backend Geliştirici)"
    },
    {
        "department": "Bilgi İşlem",
        "title": "Yetkilendirme Servisinde JWT Token Süre Dolumu Hatası ve Kullanıcı Oturum Düşmesi",
        "description": "Kullanıcıların aktif işlem yaparken her 15 dakikada bir sistemden düşmesi ve yeniden giriş yapmaya zorlanması.",
        "methodology": "5why",
        "category": "Güvenlik & Auth",
        "industry": "SaaS Platformu",
        "root_cause": "Refresh token mekanizmasındaki rotation anahtarının frontend istek senkronunda çakışarak eski tokenı geçersiz kılması.",
        "corrective_actions": "1. Refresh token için 30 saniyelik grace period (hoşgörü süresi) eklendi.\n2. Silent refresh interceptor yapısı frontend tarafında güncellendi.",
        "lessons_learned": "Kimlik doğrulama test takımlarına eşzamanlı istek (concurrency test) senaryoları eklendi.",
        "severity": 7, "occurrence": 5, "detection": 3,
        "task_title": "Refresh token grace period eklentisi ve Axios interceptor",
        "task_status": "completed",
        "assignee": "Selin Arslan (Software Lead)"
    },
    {
        "department": "Bilgi İşlem",
        "title": "Elasticsearch İndeks Boyutu Şişmesi ve Arama Yanıt Süresi Gecikmesi",
        "description": "Log analiz aramasında sorgu süresi 5 saniyenin üzerine çıktı. Disk kullanımı 1.2 TB seviyesine ulaştı.",
        "methodology": "8d",
        "category": "Arama & Veri",
        "industry": "Big Data",
        "root_cause": "Index Lifecycle Management (ILM) politikasının çalışmaması nedeniyle 90 günlük ham logların tek indekste birikmesi.",
        "corrective_actions": "1. Günlük indeks rotasyonu aktif edilip 30 günden eski veriler cold storage'a taşındı.\n2. Unused field mapping'ler indeks şablonundan kaldırıldı.",
        "lessons_learned": "Elasticsearch shard boyutları maksimum 50GB olacak şekildeotomatik bölme (rollover) kuralı eklendi.",
        "severity": 7, "occurrence": 4, "detection": 3,
        "task_title": "Elasticsearch ILM politikası yapılandırması ve rollover",
        "task_status": "in_progress",
        "assignee": "Ahmet Yılmaz (Kıdemli Bulut Mimar)"
    },
    {
        "department": "Bilgi İşlem",
        "title": "Dosya Sunucusunda Diskin %98 Doluluğa Ulaşması ve Yükleme Başarısızlığı",
        "description": "Kullanıcıların sistem dokümanı yüklerken 'HTTP 500 Insufficient Storage' hatası alması.",
        "methodology": "fishbone",
        "category": "Sistem & Depolama",
        "industry": "Kurumsal IT",
        "root_cause": "Geçici upload dosyalarının (temp files) işlem sonrası silinmeyip birikmesi ve log rotate mekanizmasının durması.",
        "corrective_actions": "1. Temp klasörü otomatik temizleyen cron görevi eklendi.\n2. Sunucuya 500GB ek NVMe depolama alanı eklendi.",
        "lessons_learned": "Disk doluluk oranı %85 olduğunda Slack ve e-posta üzerinden otomatik uyarı gönderen izleme kuralı aktif edildi.",
        "severity": 8, "occurrence": 4, "detection": 2,
        "task_title": "Temp temizleme cron görevi ve NVMe disk büyütme",
        "task_status": "completed",
        "assignee": "Deniz Er (IT Ops Manager)"
    },
    {
        "department": "Bilgi İşlem",
        "title": "SSL Sertifikası Yenileme Otomasyonunun Başarısız Olması ve Domain Uyarısı",
        "description": "Müşteri portalı alan adında SSL sertifika süresi dolduğu için tarayıcıların 'Güvenli Değil' uyarısı vermesi.",
        "methodology": "a3",
        "category": "Siber Güvenlik",
        "industry": "Web Servisleri",
        "root_cause": "Certbot otomasyonunun 80 portu HTTP challenge kontrolünde güvenlik duvarı kuralına takılması.",
        "corrective_actions": "1. DNS-01 challenge doğrulama yöntemine geçilerek Cloudflare API anahtarı entegre edildi.\n2. Yeni SSL sertifikası 2 dakikada yüklendi.",
        "lessons_learned": "SSL sertifika bitiş tarihlerine 30 gün kala otomatik kontrol yapan harici zabbix uyarısı eklendi.",
        "severity": 9, "occurrence": 2, "detection": 4,
        "task_title": "DNS-01 certbot otomasyonu ve SSL yenileme",
        "task_status": "on_hold",
        "proof_description": "Cloudflare API yetkilendirme anahtarlarının güvenlik ekibince onaylanması bekleniyor.",
        "assignee": "Burak Öz (Kıdemli Backend Geliştirici)"
    },
    {
        "department": "Bilgi İşlem",
        "title": "RabbitMQ Mesaj Kuyruğunda Birikme ve Tüketici (Worker) İşlem Durması",
        "description": "E-posta gönderim kuyruğunda 45.000 birikmiş mesaj oluşması ve kullanıcılara doğrulama kodlarının gitmemesi.",
        "methodology": "fmea",
        "category": "Mesajlaşma & Async",
        "industry": "Bulut Uygulamaları",
        "root_cause": "Celery worker süreçlerinin SMTP sunucusu zaman aşımı yanıtında takılı kalıp kilitlenmesi (deadlock).",
        "corrective_actions": "1. Celery task zaman aşımı (time_limit) 30 saniye olarak ayarlandı.\n2. Worker ölçekleme sayısı 2'den 8'e çıkarıldı.",
        "lessons_learned": "Tüm async görevlerde ack_late ve retry_backoff parametreleri zorunlu tutuldu.",
        "severity": 8, "occurrence": 4, "detection": 2,
        "task_title": "Celery worker time_limit ayarı ve yatay ölçekleme",
        "task_status": "completed",
        "assignee": "Selin Arslan (Software Lead)"
    },

    # --- FİNANS (10 Scenarios) ---
    {
        "department": "Finans",
        "title": "e-Fatura Entegratör Servisinde Zaman Aşımı ve Fatura Onay Gecikmesi",
        "description": "Gelir İdaresi Başkanlığı (GİB) entegratör servisinde onay bekleyen 240 e-faturanın 6 saat boyunca taslak durumunda kalması.",
        "methodology": "5why",
        "category": "e-Fatura & GİB",
        "industry": "Mali Hizmetler",
        "root_cause": "Entegratör firmanın SOAP API servisinde XML imzalama sertifikasının güncellenmemesi.",
        "corrective_actions": "1. Yedek özel entegratör servisine otomatik geçiş sağlandı.\n2. Hatalı faturalar yeniden imzalanarak GİB'e iletildi.",
        "lessons_learned": "e-Fatura entegratör servislerinde ikili (failover) yedekli mimariye geçildi.",
        "severity": 8, "occurrence": 4, "detection": 3,
        "task_title": "e-Fatura failover entegratör kurulumu ve XML yeniden aktarım",
        "task_status": "completed",
        "assignee": "Zeynep Avcı (Mali İşler Uzmanı)"
    },
    {
        "department": "Finans",
        "title": "Tedarikçi Cari Hesap Mutabakatında Kur Farkı Hesaplama Sapması",
        "description": "Dövizli tedarikçi hesaplarında dönem sonu değerlemesinde 145.000 TL hesaplama farkı oluşması.",
        "methodology": "8d",
        "category": "Muhasebe & Kur",
        "industry": "Kurumsal Finans",
        "root_cause": "ERP sisteminin TCMB efektif alış kuru yerine döviz satış kurunu çekmesi ve fatura tarihi yerine ödeme tarihini baz alması.",
        "corrective_actions": "1. ERP kur uyarlama tablosunda TCMB döviz alış kuru varsayılan yapıldı.\n2. Düzeltme mahsup fişi kesildi.",
        "lessons_learned": "Dönem sonu kur değerleme borç/alacak kuralları finans prosedürüne açıkça eklendi.",
        "severity": 7, "occurrence": 4, "detection": 2,
        "task_title": "ERP kur değerleme parametrelerinin revizyonu ve mahsup kaydı",
        "task_status": "in_progress",
        "assignee": "Emre Yıldız (Finansal Analist)"
    },
    {
        "department": "Finans",
        "title": "Banka Ekstre Otomatik İşleme Servisinde Format Değişikliği Hatası",
        "description": "Garanti BBVA ve İş Bankası gün sonu MT940 banka ekstrelerinin ERP muhasebe modülüne otomatik işlenememesi.",
        "methodology": "fishbone",
        "category": "Banka Entegrasyonu",
        "industry": "Bankacılık & Finans",
        "root_cause": "Bankanın MT940 dosya yapısındaki 86 alan koduna ek karakter eklemesi sonucu regex ayrıştırıcının patlaması.",
        "corrective_actions": "1. MT940 parser regex ifadesi esnek kural ile güncellendi.\n2. İşlenemeyen 85 ekstre hareketi otomatik muhasebeleştirildi.",
        "lessons_learned": "Banka dosya yapısı değişiklikleri için entegrasyon servisine hata durumunda esnek ayrıştırma modu eklendi.",
        "severity": 6, "occurrence": 5, "detection": 2,
        "task_title": "MT940 parser regex güncellemesi ve ekstre aktarımı",
        "task_status": "completed",
        "assignee": "Zeynep Avcı (Mali İşler Uzmanı)"
    },
    {
        "department": "Finans",
        "title": "Müşteri Kredi Limiti Aşımında Otomatik Sipariş Bloke Mekanizması Arızası",
        "description": "Vadesi geçmiş 200.000 TL borcu olan müşteriye sistemin otomatik sipariş onayı verip sevkiyat açması.",
        "methodology": "a3",
        "category": "Risk Yönetimi",
        "industry": "Ticari Finans",
        "root_cause": "Kredi kontrol servisinde müşteri çek risk tutarının toplam borç bakiyesinden düşülmesini sağlayan bayrağın (flag) yanlış set edilmesi.",
        "corrective_actions": "1. Kredi limit kontrol algoritması düzeltildi.\n2. Riskli sevkiyat yola çıkmadan durduruldu.",
        "lessons_learned": "Risk limiti aşan siparişlerde sadece sistem engeli değil, Finans Müdürü e-posta onayı zorunluluğu da getirildi.",
        "severity": 9, "occurrence": 3, "detection": 3,
        "task_title": "Kredi limit algoritması kural düzeltmesi ve sipariş blokesi",
        "task_status": "completed",
        "assignee": "Emre Yıldız (Finansal Analist)"
    },
    {
        "department": "Finans",
        "title": "Ay Sonu Amortisman Hesaplama Tablosunda Yuvarlama Farkı Uyumsuzluğu",
        "description": "Sabit kıymetler amortisman defteri ile genel mizan arasında 1.240 TL yuvarlama farkı tespit edilmesi.",
        "methodology": "fmea",
        "category": "Mizan & Amortisman",
        "industry": "Mali Kontrol",
        "root_cause": "Kıdemli sabit kıymet yazılımının virgülden sonra 2 hane yerine 4 hane çalışıp yuvarlamayı son adımda yapması.",
        "corrective_actions": "1. Amortisman modülü virgülden sonra 2 hane standart kuruş yuvarlamasına çekildi.\n2. Fark tutarı kıdemli amortisman gider hesabına aktarıldı.",
        "lessons_learned": "Sabit kıymet modülü hesaplamaları ay sonu kapanış checklist'inde otomatik çapraz kontrole bağlandı.",
        "severity": 5, "occurrence": 5, "detection": 2,
        "task_title": "Amortisman modülü virgül yuvarlama ayarı ve mahsup",
        "task_status": "todo",
        "assignee": "Zeynep Avcı (Mali İşler Uzmanı)"
    },
    {
        "department": "Finans",
        "title": "İthalat KDV Tevkifatı Muhasebeleştirme Kodlama Hatası ve Beyanname Düzeltmesi",
        "description": "Yurtdışı hizmet alımı KDV 2 beyannamesinde 9015 KDV tevkifat kodunun yanlış hesaba işlenmesi sebebiyle vergi dairesi uyarısı.",
        "methodology": "5why",
        "category": "Vergi & Mevzuat",
        "industry": "Mali Danışmanlık",
        "root_cause": "Stajyer muhasebe elemanının fatura girişinde varsayılan vergi kodunu seçmesi ve onay mekanizmasından kaçması.",
        "corrective_actions": "1. Düzeltme KDV 2 beyannamesi verilip fark ödendi.\n2. ERP fatura girişinde 1000 TL üzeri tüm işlemlere Finans Uzmanı onayı eklendi.",
        "lessons_learned": "Yurtdışı fatura girişlerinde Vergi Kodu alanı otomatik öneri yerine zorunlu seçimli hale getirildi.",
        "severity": 8, "occurrence": 3, "detection": 4,
        "task_title": "Düzeltme KDV 2 beyannamesi verilmesi ve ERP onay kuralı",
        "task_status": "completed",
        "assignee": "Emre Yıldız (Finansal Analist)"
    },
    {
        "department": "Finans",
        "title": "Personel Masraf Onay Akışında Mobil Onay Gecikmesi ve Ödeme Ertelemesi",
        "description": "Saha satış personelinin masraf formlarının 3 hafta boyunca onay bekleyerek personel mağduriyeti yaratması.",
        "methodology": "8d",
        "category": "Masraf Yönetimi",
        "industry": "Kurumsal Yönetim",
        "root_cause": "Masraf mobil uygulamasının bildirim (push notification) servisinin iOS 17 güncellemesinde çalışmaması.",
        "corrective_actions": "1. Mobil uygulama push notification APNS kütüphanesi güncellendi.\n2. 3 günü geçen onaylarda otomatik üst yöneticiye eskalasyon eklendi.",
        "lessons_learned": "Masraf ödemeleri her hafta Cuma günü standart otomatik EFT akışına bağlandı.",
        "severity": 6, "occurrence": 6, "detection": 2,
        "task_title": "Mobil masraf push notification güncellemesi ve eskalasyon",
        "task_status": "in_progress",
        "assignee": "Zeynep Avcı (Mali İşler Uzmanı)"
    },
    {
        "department": "Finans",
        "title": "Dönemsel Bütçe Sapma Analizinde Hatalı Maliyet Merkezi Ataması",
        "description": "Pazarlama departmanı lansman harcamalarının 450.000 TL'lik kısmının yanlışlıkla IT maliyet merkezine yazılması.",
        "methodology": "fishbone",
        "category": "Bütçe & Raporlama",
        "industry": "Bütçe Kontrol",
        "root_cause": "Satın alma siparişi (PO) açılırken varsayılan masraf merkezinin değiştirilmeden kaydoluşu.",
        "corrective_actions": "1. 450.000 TL tutarındaki fatura Pazarlama Maliyet Merkezi'ne virmanlandı.\n2. PO oluşturma ekranında Masraf Merkezi seçimi zorunlu kılındı.",
        "lessons_learned": "Bütçe sapma raporları her ayın 5. günü maliyet merkezi yöneticilerine otomatik e-posta gönderilecek.",
        "severity": 7, "occurrence": 4, "detection": 3,
        "task_title": "Maliyet merkezi virman kaydı ve PO ekranı zorunlu alan ayarı",
        "task_status": "completed",
        "assignee": "Emre Yıldız (Finansal Analist)"
    },
    {
        "department": "Finans",
        "title": "Teminat Mektubu Süre Takip Sisteminde Hatırlatma E-postası Gönderilmeyişi",
        "description": "2.5 Milyon TL tutarındaki ihale teminat mektubunun süresinin dolmasına 5 gün kala komisyon masrafı ödenmediği için mektubun nakde çevrilme riski.",
        "methodology": "a3",
        "category": "Hazine & Teminat",
        "industry": "Hazine Yönetimi",
        "root_cause": "SMTP sunucusundaki port değişikliği sonrası teminat mektubu takip modülü e-posta servisinin hata vermesi.",
        "corrective_actions": "1. Banka ile görüşülüp teminat mektubu süresi 6 ay uzatıldı ve komisyon ödendi.\n2. E-posta servis bağlantısı TLS 587 portu ile güncellendi.",
        "lessons_learned": "Kritik hazine ve teminat işlemleri için e-posta yanında SMS bilgilendirme servisi devreye alındı.",
        "severity": 9, "occurrence": 2, "detection": 4,
        "task_title": "Teminat mektubu vade uzatımı ve SMS bildirim servisi",
        "task_status": "on_hold",
        "proof_description": "İlgili kamu idaresinden yeni ihale zeyilname belgesi bekleniyor.",
        "assignee": "Zeynep Avcı (Mali İşler Uzmanı)"
    },
    {
        "department": "Finans",
        "title": "Nakit Akış Tahmin Modülünde Vadeli Çek Tahsilat Zamanı Yanılgısı",
        "description": "Gelecek ay nakit akış tahmininde 1.8 Milyon TL açık oluşması sebebiyle kredi hattı kullanımına ihtiyaç duyulması.",
        "methodology": "fmea",
        "category": "Nakit Akışı",
        "industry": "Kurumsal Hazine",
        "root_cause": "Müşterilerden alınan vadeli çeklerin takasa verilme gün sayısı ile valör tarihinin tahmin modeline eklenmemesi.",
        "corrective_actions": "1. Nakit akış projeksiyon algoritmasına +2 gün takas valör süresi eklendi.\n2. Banka rotatif kredi hattı opsiyonel olarak hazır tutuldu.",
        "lessons_learned": "Nakit akış modellerinde çek tahsilatlarında muhafazakar +3 gün valör kuralı standartlaştırıldı.",
        "severity": 8, "occurrence": 4, "detection": 3,
        "task_title": "Nakit akış projeksiyon algoritması valör revizyonu",
        "task_status": "completed",
        "assignee": "Emre Yıldız (Finansal Analist)"
    }
]

async def seed_database():
    print("=== PROBY AI SEED DATA GENERATION STARTED ===")
    async with async_session_factory() as session:
        # 1. Fetch or ensure test user
        res = await session.execute(select(User).limit(1))
        user = res.scalar_one_or_none()
        if not user:
            print("No user found in DB! Creating admin user first...")
            from app.core.security import hash_password
            user = User(
                email="admin@proby.ai",
                hashed_password=hash_password("admin123"),
                full_name="Sistem Yöneticisi",
                role="admin",
                is_active=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        user_id = user.id
        print(f"Using User ID: {user_id}")

        # 2. Clear old data from DB
        print("Clearing old test data...")
        await session.execute(delete(AuditLog))
        await session.execute(delete(Task))
        await session.execute(delete(ProblemRecordORM))
        await session.execute(delete(ProblemSession))
        await session.commit()
        print("Database tables purged successfully.")

        # 3. Setup Qdrant Repository and recreate collection
        qdrant_repo = QdrantRepository(vector_size=3072)
        try:
            print("Re-creating Qdrant vector collection 'knowledge_records'...")
            try:
                qdrant_repo._client.delete_collection(qdrant_repo._collection_name)
            except Exception:
                pass
            qdrant_repo.ensure_collection()
            print("Qdrant collection reset successfully.")
        except Exception as q_err:
            print(f"Warning/Error with Qdrant collection reset: {q_err}")

        # 4. Instantiate Embedding Pipeline
        from app.infrastructure.llm.gemini_client import GeminiClient
        gemini_client = GeminiClient(settings.gemini_api_key, settings.gemini_llm_model, "models/gemini-embedding-001")
        embedding_service = EmbeddingService(client=gemini_client)
        pipeline = EmbeddingPipeline(embedding_service=embedding_service, qdrant_repository=qdrant_repo)

        # 5. Generate 50 Scenarios
        created_records_count = 0
        created_tasks_count = 0

        now = datetime.now(timezone.utc)

        for idx, scenario in enumerate(SCENARIOS, 1):
            created_at = now - timedelta(days=(50 - idx))
            
            # AI Agent turn-by-turn chat history for problem solving
            chat_history = [
                {
                    "role": "assistant",
                    "content": f"👋 Merhaba! **{scenario['department']}** departmanı bünyesinde **\"{scenario['title']}\"** başlıklı problem oturumu başlatıldı.\n\nİnceleme Modülü: **{scenario['methodology'].upper()} Metodolojisi**\n\n📌 **Problem Tanımı**: {scenario['description']}\n\nLütfen saha gözlemlerinizi ve ilk teknik bulguları paylaşın."
                },
                {
                    "role": "user",
                    "content": f"Saha ekibi ve teknik uzmanımız ({scenario['assignee']}) ile inceleme gerçekleştirdik. Yapılan analiz sonucunda kök nedenin **\"{scenario['root_cause']}\"** olduğunu tespit ettik."
                },
                {
                    "role": "assistant",
                    "content": f"🛠️ **Kök Neden Doğrulandı!**\n\n**Önerilen Düzeltici ve Önleyici Faaliyetler (DÖF)**:\n{scenario['corrective_actions']}\n\n🔒 **Yokoten & Yaygınlaştırma Standardı**:\n{scenario['lessons_learned']}\n\nAksiyonların uygulanması tamamlandığında kapatma ve A3 raporu üretme aşamasına geçilebilir."
                },
                {
                    "role": "user",
                    "content": f"Düzeltici ve önleyici faaliyetlerin hepsi başarıyla sahada uygulandı, kalibrasyon ve performans testleri tamamlandı. SOP dokümanı eklendi. Problem kaydını kapatabiliriz."
                },
                {
                    "role": "assistant",
                    "content": f"🎉 **Tebrikler!** Vaka kaydı başarıyla **KAPATILDI** ve onaylandı.\n\n✅ Kök Neden Çözüldü\n✅ DÖF Aksiyonu Uygulandı\n✅ Yokoten Standardı Yayınlandı\n✅ A3 Özet Raporu Oluşturuldu ve Qdrant Vektör Hafızasına İndekslendi."
                }
            ]

            # Create ProblemSession
            prob_session = ProblemSession(
                owner_id=user_id,
                methodology=scenario["methodology"],
                problem_description=scenario["description"],
                department=scenario["department"],
                status=SessionStatus.COMPLETED.value,
                agent_status="closed",
                assignee_name=scenario["assignee"],
                tracker_name="Proby AI Agent",
                summary=f"Problem: {scenario['title']}\nKök Neden: {scenario['root_cause']}\nÇözüm: {scenario['corrective_actions']}\nYokoten: {scenario['lessons_learned']}",
                agent_chat_history=chat_history,
                step_data={
                    "answers": {
                        "problem_definition": scenario["description"],
                        "kök_neden": scenario["root_cause"],
                        "aksiyonlar": scenario["corrective_actions"],
                        "yokoten": scenario["lessons_learned"]
                    }
                },
                step_responses={
                    "problem_definition": scenario["description"],
                    "kök_neden": scenario["root_cause"],
                    "aksiyonlar": scenario["corrective_actions"],
                    "yokoten": scenario["lessons_learned"]
                },
                created_at=created_at,
                updated_at=created_at
            )
            session.add(prob_session)
            await session.flush()

            # Create ProblemRecordORM (ALL 50 CLOSED)
            rpn_val = scenario["severity"] * scenario["occurrence"] * scenario["detection"]
            record = ProblemRecordORM(
                session_id=prob_session.id,
                user_id=user_id,
                title=scenario["title"],
                description=scenario["description"],
                methodology=scenario["methodology"],
                industry=scenario["industry"],
                department=scenario["department"],
                problem_category=scenario["category"],
                root_cause=scenario["root_cause"],
                corrective_actions=scenario["corrective_actions"],
                lessons_learned=scenario["lessons_learned"],
                severity=scenario["severity"],
                occurrence=scenario["occurrence"],
                detection=scenario["detection"],
                rpn=rpn_val,
                yokoten_applied=True,
                closure_checklist={
                    "yokoten_scope": f"{scenario['department']} bünyesindeki tüm ilgili hat, ekipman ve standart operasyon prosedürlerine (SOP) yatay olarak yaygınlaştırıldı ve uygulandı.",
                    "checklist": [
                        f"{scenario['methodology'].upper()} Kök Neden Analizi ve Doğrulaması Tamamlandı",
                        f"Tedarik/Teknik Kök Neden: {scenario['root_cause'][:60]}...",
                        "Düzeltici ve Önleyici Faaliyetler (DÖF) Sahada Uygulandı",
                        "Saha Kalite Onayı ve Performans Kalibrasyonu Alındı",
                        f"Yokoten (Yatay Yayılım) Standardı {scenario['department']} Biriminde Yayınlandı",
                        "A3 Kapanış Özet Raporu ve SOP Dokümanları Arşivlendi",
                        "Qdrant Kurumsal Beyin Vektör Hafızasına Kaydedildi"
                    ],
                    "completed_by": scenario["assignee"],
                    "approved_by": "Yönetici Onaylı (admin@proby.ai)"
                },
                resolution_status="closed",
                resolution_date=created_at + timedelta(days=2),
                meta_data={
                    "resolution_chat_history": chat_history,
                    "assignee_name": scenario["assignee"],
                    "tracker_name": "Proby AI Agent",
                    "documents": [
                        {
                            "id": str(uuid.uuid4()),
                            "file_name": f"{scenario['department']}_SOP_Kapanis_Raporu.pdf",
                            "file_size": 1024 * 420,
                            "content_type": "application/pdf",
                            "uploaded_at": (created_at + timedelta(days=2)).isoformat()
                        }
                    ],
                    "ai_agent_summary": f"Vaka: {scenario['title']}. Kök Neden: {scenario['root_cause']}. Çözüm başarıyla tamamlandı ve Yokoten ile tüm hatlara uygulandı.",
                    "report_pdf_generated": True
                },
                embedding_status=EmbeddingStatus.PENDING.value,
                created_at=created_at,
                updated_at=created_at
            )
            session.add(record)
            await session.flush()
            created_records_count += 1

            # Create Linked Task (ALL 50 COMPLETED)
            task = Task(
                problem_record_id=record.id,
                session_id=prob_session.id,
                title=scenario["task_title"],
                description=f"Kök neden çözümü için aksiyon: {scenario['root_cause']}",
                assignee_name=scenario["assignee"],
                department=scenario["department"],
                priority="high" if rpn_val > 150 else "medium",
                deadline=created_at + timedelta(days=5),
                status="completed",
                proof_description=f"Tüm düzeltici aksiyonlar sahada başarıyla uygulandı, kalite testleri onaylandı: {scenario['corrective_actions']}",
                proof_url=f"https://docs.proby.ai/reports/{scenario['department'].lower()}_kapanis.pdf",
                created_at=created_at,
                updated_at=created_at + timedelta(days=2)
            )
            session.add(task)
            created_tasks_count += 1

            # Audit Log for closed record
            audit_log = AuditLog(
                user_id=user_id,
                operation="CLOSE_RECORD",
                entity_type="problem_record",
                entity_id=record.id,
                before_state={"resolution_status": "open"},
                after_state={"resolution_status": "closed", "task_status": "completed"},
                before_values={"status": "active"},
                after_values={"status": "closed"},
                created_at=created_at + timedelta(days=2)
            )
            session.add(audit_log)

            # Process Qdrant Embedding
            embedding_text = f"{record.title}\n{record.description}\n{record.lessons_learned}"
            embedding_payload = {
                "title": record.title,
                "methodology": record.methodology,
                "industry": record.industry,
                "department": record.department,
            }
            try:
                ok = pipeline.process(record.id, embedding_text, embedding_payload)
                record.embedding_status = EmbeddingStatus.COMPLETED.value if ok else EmbeddingStatus.FAILED.value
            except Exception as emb_err:
                print(f"Embedding error for record #{idx} ({record.title}): {emb_err}")
                record.embedding_status = EmbeddingStatus.FAILED.value

            if idx % 10 == 0:
                print(f"Processed {idx}/50 scenarios...")

        await session.commit()
        print("--------------------------------------------------")
        print(f"SUCCESSFULLY GENERATED:")
        print(f" -> {created_records_count} Problem Records across 5 Departments")
        print(f" -> {created_tasks_count} Linked Action Plan Tasks")
        print(f" -> Vector Embeddings indexed in Qdrant")
        print("==================================================")

if __name__ == "__main__":
    asyncio.run(seed_database())
