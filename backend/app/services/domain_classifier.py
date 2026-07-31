from enum import Enum
import re


class ProblemDomain(str, Enum):
    IT_INFRASTRUCTURE = "Bilgi İşlem / Altyapı & Yazılım"
    MANUFACTURING = "Üretim & İmalat"
    LOGISTICS = "Lojistik & Tedarik Zinciri"
    GENERAL_QUALITY = "Kalite & Süreç"


def detect_problem_domain(text: str) -> ProblemDomain:
    """Metindeki anahtar kelimelere gore problem alanini tespit eder."""
    lowered = text.lower()

    it_keywords = [
        "sunucu", "sanal sunucu", "vmware", "nutanix", "hipervizör", "hypervisor",
        "api", "mikroservis", "veritabanı", "database", "yazılım", "network", "dns",
        "cloud", "bulut", "docker", "kubernetes", "ip", "port", "bağlantı", "kod",
        "hata", "latens", "gecikme", "deploy", "sunucuda", "uygulama", "virtio", "storage pool"
    ]

    manufacturing_keywords = [
        "pres", "enjeksiyon", "cnc", "kalıp", "montaj", "imalat", "makine", "çapak",
        "kalibrasyon", "tezgah", "motor", "hidrolik", "tolerans", "üretim hattı", "parça",
        "sıcaklık kontrol", "vida", "mil"
    ]

    logistics_keywords = [
        "depo", "stok", "kargo", "sevkiyat", "nakliye", "palet", "tedarik", "raf",
        "teslimat", "transfer", "soğuk depo", "kompresör"
    ]

    it_score = sum(1 for kw in it_keywords if kw in lowered)
    mfg_score = sum(1 for kw in manufacturing_keywords if kw in lowered)
    log_score = sum(1 for kw in logistics_keywords if kw in lowered)

    if it_score > 0 and it_score >= mfg_score and it_score >= log_score:
        return ProblemDomain.IT_INFRASTRUCTURE
    elif mfg_score > 0 and mfg_score >= log_score:
        return ProblemDomain.MANUFACTURING
    elif log_score > 0:
        return ProblemDomain.LOGISTICS
    else:
        return ProblemDomain.GENERAL_QUALITY


def get_domain_persona(domain: ProblemDomain) -> str:
    """Problemin alanina uygun AI Uzman personasini dondurur."""
    if domain == ProblemDomain.IT_INFRASTRUCTURE:
        return (
            "Sen 20+ yıllık tecrübeye sahip Kıdemli Bulut Mimarisi, Sistem Yönetimi ve DevOps Kök Neden Analizi Uzmanısın (Senior SRE & Cloud Architect). "
            "Sanal sunucu migrasyonları (VMware -> Nutanix AHV/KVM), VirtIO/vNIC sürücüleri, DNS/IP routing, depolama (storage pool/UUID mount), "
            "uygulama bağımlılıkları ve yetkilendirme katmanları konularında uzmansın."
        )
    elif domain == ProblemDomain.MANUFACTURING:
        return (
            "Sen 20+ yıllık tecrübeye sahip Yalın Üretim, TPM ve Endüstriyel Üretim Kök Neden Analizi Uzmanısın (Lean & TPS Master Black Belt). "
            "Ekipman kalibrasyonu, hidrolik/pnömatik basınç, kalıp toleransları, malzeme spesifikasyonları ve süreç parametreleri konularında uzmansın."
        )
    elif domain == ProblemDomain.LOGISTICS:
        return (
            "Sen Kıdemli Lojistik, Soğuk Zincir ve Depo Operasyonları Kök Neden Analizi Uzmanısın. "
            "Stok senkronizasyonu, sensör sapmaları, ortam iklimlendirme ve ERP/WMS entegrasyonları konularında uzmansın."
        )
    else:
        return (
            "Sen Kıdemli Süreç Yönetimi, Kalite Güvence ve Kök Neden Analizi Uzmanısın."
        )


def get_domain_adaptive_fallback(domain: ProblemDomain, problem_desc: str, last_ans: str | None = None) -> str:
    """LLM cagrisi zaman asimina ugradiginda alana ozel dinamik soru olusturur."""
    target = last_ans[:50] if last_ans else problem_desc[:50]

    if domain == ProblemDomain.IT_INFRASTRUCTURE:
        return (
            f"'{target}' aksaklığı değerlendirildiğinde; geçiş/çalışmama durumunun arkasında "
            f"1) Sanallaştırma sürücü (VirtIO/vNIC) ve depolama mount (UUID) uyumsuzluğu mu, yoksa "
            f"2) Ağ/DNS konfigürasyon ve yetkilendirme erişim kısıtı mı rol oynadı? Hangi hata günlüğü (log) gözleniyor?"
        )
    elif domain == ProblemDomain.MANUFACTURING:
        return (
            f"'{target}' aksaklığı değerlendirildiğinde; bu sapmanın arkasında "
            f"1) Ekipman/parça kalibrasyon ve mekanik aşınması mı, yoksa "
            f"2) Operasyonel süreç parametresi ve hammadde/girdi sapması mı var?"
        )
    elif domain == ProblemDomain.LOGISTICS:
        return (
            f"'{target}' aksaklığı değerlendirildiğinde; problemin arkasında "
            f"1) Sensör/iklimlendirme donanım sapması mı, yoksa "
            f"2) WMS/ERP stok veri senkronizasyon hatası mı rol oynadı?"
        )
    else:
        return (
            f"'{target}' aksaklığı değerlendirildiğinde; bu durumun arkasındaki "
            f"doğrudan teknik veya operasyonel temel etken nedir?"
        )
