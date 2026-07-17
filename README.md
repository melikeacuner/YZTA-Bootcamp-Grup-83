# **Takım İsmi**
Takım 83
# **Ürün İle İlgili Bilgiler**
## **Takım Elemanları**
- Melisa Özkılıç : Product Owner 
- Melike Acuner : Scrum Master
- Şevket Binali : Developer
- Merve Yüsra Bektaş : Developer
## **Ürün İsmi**
Proby AI
## **Ürün Açıklaması**
Kurumsal süreçlerde oluşan problemleri sistematik metodolojiler ve yapay zeka desteğiyle analiz eden, çözüm süreçlerini dijital hafızaya dönüştüren bir bilgi yönetim platformudur.
## **Ürün Özellikleri**
- Akıllı problem girişi (AI ile özetleme, etiketleme)  
- Semantik arama (RAG) ile benzer vakaları bulma  
- AI destekli kök neden analizi (5 Why, Ishikawa, 8D)  
- Adım adım çözüm süreci yönetimi  
- Kurumsal bilgi havuzu oluşturma  

## **Hedef Kitle**
- Üretim ve endüstriyel firmalar  
- IT ve teknoloji ekipleri  
- Kurumsal şirketler (enterprise)  
- Operasyon ve kalite ekipleri  
- Müşteri destek ekipleri  

# **Sprint 1**
Sprint içinde tamamlanması tahmin edilen puan: 100 Puan
Puan tamamlama mantığı: Proje boyunca tamamlanması gereken toplam 300 puanlık backlog bulunmaktadır. 3 sprinte bölündüğünde ilk sprintin 100 ile başlaması gerektiği kararlaştırıldı.  

### - Backlog düzeni ve Story seçimleri:
Backlog'umuz bir sonraki sprintlerin temelini atacak şekilde düzenlenmiştir. Sprint başına tahmin edilen puan sayısını geçmeyecek şekilde görevler dağıtılmıştır. ClickUp'ta gözüken gri item'lar yapılacak işleri, mavi item'lar yapılmakta olan işleri, yeşil item'lar yapılmış işleri temsil etmektedir. Sprint sonu günleri ekibin dinlenmesi amacıyla boş bırakılmıştır.

### - Daily Scrum:
Daily Scrum toplantıları ekip yoğunlukları nedeniyle her gün düzenli yapılamamış, haftalık olarak Slack ve Google Meet üzerinden gerçekleştirilmiştir.
Toplantı ScreenShotları :
<img width="2360" height="1470" alt="IMG_1284" src="https://github.com/user-attachments/assets/f2976faf-f4cc-4a23-a3ad-9f1095cb273a" />


### - Sprint board update: Sprint board screenshot:
<img width="1143" height="864" alt="image (1)" src="https://github.com/user-attachments/assets/c4a84745-ec81-4bc9-890a-a1ed2b67d80d" />

### - Ürün Durumu: Ekran görüntüleri:
<img width="1600" height="781" alt="giriş" src="https://github.com/user-attachments/assets/1a26f222-9b8b-4346-b6d7-810366464650" />

<img width="1600" height="787" alt="yeniproblem" src="https://github.com/user-attachments/assets/4996aa98-421c-4bba-85a3-eacf8c90d775" />

### - Sprint Review:
Bu sprintte projenin temel yapısı netleştirildi ve güçlü bir başlangıç yapıldı. Ürünün amacı, kapsamı ve teknik mimarisi belirlenerek geliştirme süreci için sağlam bir zemin oluşturuldu. Problem çözme yaklaşımları, AI entegrasyonu ve RAG altyapısı planlandı, arayüz tasarımına başlanarak sistemin nasıl çalışacağı somutlaştırıldı. Genel olarak sprint hedeflerine büyük ölçüde ulaşıldı ve proje artık geliştirme aşamasına geçmeye hazır hale geldi. Sprint Review katılımcıları: Melisa Özkılıç, Melike Acuner, Şevket Binali, Merve Yüsra Bektaş.

### - Sprint Retrospective:
Sprint genel olarak verimli geçti ancak bazı teknik konuların beklenenden daha karmaşık olduğu görüldü. Özellikle AI ve RAG tarafında daha fazla araştırma ihtiyacı ortaya çıktı. UI/UX tarafında geliştirme başlamadan önce daha net tasarım kararları alınmasının süreci hızlandıracağı fark edildi. Bir sonraki sprintte daha küçük ve net görevler belirlenerek ilerlemek, bağımlılıkları daha iyi yönetmek ve çalışan bir MVP odaklı ilerlemek süreci daha verimli hale getirecektir.Genel olarak ekip uyumu ve iletişimi başarılı ilerlemiştir.

# **Sprint 2**

Bu sprintte ürünün teknik temeli sıfırdan hayata geçirildi: kimlik doğrulama, dört problem
çözme metodolojisi (Ishikawa, 8D, 5 Why, PDCA), yapay zeka destekli bilgi bankası ve bunları
birbirine bağlayan uçtan uca bir REST API ile kullanıcı arayüzü tamamlandı. Aşağıda bu
sprintte kurulan mimarinin ve geliştirme ortamının özeti yer almaktadır.

### - Teknoloji Yığını:

| Katman | Teknoloji | Görevi |
| --- | --- | --- |
| **Frontend** | Next.js 14, TypeScript, Vanilla CSS | Kullanıcı arayüzü |
| **Backend** | FastAPI (Python), SQLAlchemy 2.0 (async) | REST API ve iş mantığı |
| **Yapay Zeka** | Google Gemini (LLM + embedding) | Takip sorusu üretimi, özetleme, semantik arama |
| **Vektör Veritabanı** | Qdrant | RAG tabanlı benzer vaka araması |
| **İlişkisel Veritabanı** | PostgreSQL | Kullanıcı, oturum ve kayıt yönetimi |
| **Önbellek / Kuyruk** | Redis + Celery | Arama önbelleği, embedding yeniden deneme kuyruğu |

### - Proje Yapısı:

```
.
├── backend/            # FastAPI uygulaması (app/{core,domain,api,services,infrastructure})
├── frontend/            # Next.js 14 + TypeScript uygulaması
├── docker-compose.yml   # postgres, redis, qdrant, backend, celery-worker, frontend orkestrasyonu
└── .env.example          # gerekli ortam değişkenlerinin şablonu
```

### - Geliştirme Ortamı Kurulumu:

1. **Ön koşullar:** [Docker Desktop](https://www.docker.com/products/docker-desktop/), Git.
2. `.env.example` dosyasını `.env` olarak kopyalayın ve gerekli değerleri doldurun
   (özellikle `GEMINI_API_KEY`, `JWT_SECRET_KEY`).
3. Tüm servisleri tek komutla ayağa kaldırın:
   ```bash
   docker compose up --build
   ```
4. Servisler hazır olduğunda:
   - Backend → http://localhost:8000 &nbsp;(health: `/health`, docs: `/docs`)
   - Frontend → http://localhost:3000
   - Qdrant → http://localhost:6333
5. Backend testlerini yerelde çalıştırmak için (Python 3.11+ ile):
   ```bash
   cd backend
   pip install -r requirements-dev.txt
   pytest -v
   ```

### - Sprint Review:
Bu sprintte ürünün teknik iskeleti, sadece mimari kararların ötesine geçerek çalışan ve
test edilmiş bir sisteme dönüştü. Geliştirme, birbirinin üzerine inşa edilen beş branch/pull
request ile ilerledi: backend (FastAPI) ve frontend (Next.js) iskeleti, Pydantic domain
modelleri, PostgreSQL şeması (SQLAlchemy 2.0 + Alembic) ve docker-compose orkestrasyonu;
JWT kimlik doğrulama, RBAC, audit logging ve dört metodolojinin (Ishikawa, 8D, 5 Why, PDCA)
adım motorları ile SessionService; Google Gemini tabanlı LLM/embedding servisleri, Qdrant,
RAG semantik arama, Redis önbellekleme ve Celery yeniden deneme kuyruğu; auth/oturum/bilgi
bankası/kayıt uç noktalarını içeren REST API, rate limiting ve merkezi hata yönetimi; son
olarak giriş/kayıt, problem oturumu ve bilgi bankası arama sayfaları ile Celery worker.
Her branch anlamlı commit'lerle ilerletildi, testlerle doğrulandı ve PR review'dan geçirilerek
main'e alındı. Backend'de 96 test başarıyla geçti, frontend derleme/typecheck/lint hatasız
tamamlandı ve sistem gerçek bir sunucuda ayağa kaldırılarak doğrulandı. Proje artık gerçek
altyapı (Docker, PostgreSQL, Qdrant, Redis, bir Gemini API anahtarı) ile uçtan uca denenmeye
hazır durumda.

### - Sprint Retrospective:
Sprint verimli geçti; beş parçaya bölünmüş, birbirinin üzerine inşa edilen branch yapısı
işi yönetilebilir tutmayı ve her aşamayı ayrı ayrı test edip doğrulamayı kolaylaştırdı.
Buna karşılık kullanılan bazı üçüncü parti bileşenlerin (ör. seçilen Gemini model adları)
kısa sürede kullanımdan kalkması, bağımlılıkları düzenli kontrol etmenin önemini gösterdi.
Ayrıca geliştirme ortamında karşılaşılan disk alanı kısıtı gibi altyapısal sorunlar, ortam
hazırlığının sprint başında netleştirilmesi gerektiğini ortaya koydu. Bir sonraki sprintte
gerçek bir Gemini API anahtarıyla uçtan uca doğrulama yapmak, Docker Compose ile tüm
servisleri birlikte test etmek ve frontend tarafında kullanıcı deneyimini derinleştirmek
öncelikli hedefler olacak.
