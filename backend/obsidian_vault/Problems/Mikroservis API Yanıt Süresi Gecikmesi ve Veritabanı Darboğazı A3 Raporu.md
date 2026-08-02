---
id: 54fcfffb-e619-4e6d-b581-6d9d1e2a26bd
title: "Mikroservis API Yanıt Süresi Gecikmesi ve Veritabanı Darboğazı A3 Raporu"
department: "Bilgi İşlem"
methodology: "5why"
severity: 6
occurrence: 6
detection: 2
rpn: 72
status: "closed"
assignee: "Burak Öz (Kıdemli Backend Geliştirici)"
tracker: "Selin Arslan (Software Lead)"
tags:
  - performance
  - Redis Cache
  - Mikroservis
  - PostgreSQL
  - diğer
  - Performans Optimizasyonu
  - postgresql
  - api
  - 5why
  - Veritabanı İndeksi
yokoten_applied: false
created_at: "2026-07-23T22:18:02.480336+00:00"
closed_at: "2026-08-02T09:02:51.574606+00:00"
created_by: "Kullanici"
---

# [[Problems/Mikroservis API Yanıt Süresi Gecikmesi ve Veritabanı Darboğazı A3 Raporu|Mikroservis API Yanıt Süresi Gecikmesi ve Veritabanı Darboğazı A3 Raporu]]

## 🔍 Problem Açıklaması
Ödeme ve sipariş onay mikroservisinde yoğun saatlerde (14:00 - 16:00) ortalama yanıt süresi 45ms'den 450ms'ye yükseliyor, zaman aşımı hataları oluşuyor.

## 👥 Atamalar & Tarihler
- **Sorumlu (Assignee):** Burak Öz (Kıdemli Backend Geliştirici)
- **Denetçi (Tracker):** Selin Arslan (Software Lead)
- **Açılış Tarihi:** 23.07.2026 22:18
- **Kapanış Tarihi:** 02.08.2026 09:02

## 🧠 Kök Neden (Root Cause)
Ödeme ve sipariş onay mikroservisinde yoğun yük saatlerinde (14:00 - 16:00) yanıt sürelerinin 45ms'den 450ms'ye yükselmesinin ve zaman aşımı hatalarının oluşmasının temel kök nedeni; veritabanı bağlantı havuzu (connection pool) sınırının yetersiz tanımlanmış olması (max_connections=20) ve `orders` tablosundaki sorgularda uygun indeks bulunmaması nedeniyle PostgreSQL veritabanı üzerinde Sequential Scan (sıralı tarama) yapılarak sistem kaynaklarının (CPU/IO) kilitlenmesidir.

## 🎓 Alınan Dersler (Lessons Learned)
Kök Neden: Düşük bağlantı havuzu limiti ve indekssiz veritabanı sorgularının yoğun saatlerde oluşturduğu yüksek G/Ç darboğazı.
Düzeltici Eylemler: Veritabanı sorgularının indekslenmesi, bağlantı havuzu boyutunun artırılması ve Redis önbellek katmanının devreye alınması.
Sonuç: Yoğun saatlerdeki ortalama API yanıt süreleri tekrar 45ms seviyesine düşürülmüş, zaman aşımı (timeout) hataları tamamen ortadan kaldırılmıştır.
Önleyici Öneriler: Canlıya alınacak tüm mikroservisler için yük ve stres testlerinin zorunlu hale getirilmesi, kod gözden geçirme (code review) süreçlerinde sorgu yürütme planlarının (EXPLAIN ANALYZE) denetlenmesi denetim listelerine eklenmelidir.

## 📊 Risk Değerlendirmesi & FMEA
| Şiddet (S) | Olasılık (O) | Saptanabilirlik (D) | RPN |
| :---: | :---: | :---: | :---: |
| 6 | 6 | 2 | **72** |

### 📋 Kapatma Kontrol Listesi
- [x] checklist


## 🛠️ Düzeltici Eylemler & Aksiyonlar
- [[Tasks/Aksiyon- Mikroservis API Yanıt Süresinde 450ms Gecikme|Aksiyon: Mikroservis API Yanıt Süresinde 450ms Gecikme]] — Sorumlu: **Burak Öz (Kıdemli Backend Geliştirici)** — Durum: `completed`



## 💬 Çözüm Sohbeti & AI Önerileri
**Kullanıcı:** Bu problem için kök neden ve çözüm önerileriniz nelerdir?

**AI Çözüm Ajanı:** Probleminiz detaylı incelendi. Kök neden: Veritabanı bağlantı havuzunun (connection pool) max_connections=20 ile sınırlandırılmış olması ve indeks bulunmayan sipariş sorgusunun PostgreSQL üzerinde Sequential Scan yapması.
Planlanan eylemler: 1. `CREATE INDEX idx_orders_user_created ON orders(user_id, created_at DESC)` indeksi eklendi.
2. Bağlantı havuzu boyutu 50'ye çıkarıldı ve Redis önbellek katmanı eklendi.



## 🔗 Sistem Bağlantıları
- Departman: [[Departments/Bilgi İşlem|Bilgi İşlem]]
- Metodoloji: [[Methodologies/5why|5why Metodolojisi]]
- Yokoten Uygulandı mı: **Hayır**
