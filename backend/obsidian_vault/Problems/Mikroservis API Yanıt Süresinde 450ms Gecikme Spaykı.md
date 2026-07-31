---
id: 54fcfffb-e619-4e6d-b581-6d9d1e2a26bd
title: "Mikroservis API Yanıt Süresinde 450ms Gecikme Spaykı"
department: "Bilgi İşlem"
methodology: "5why"
severity: 6
occurrence: 6
detection: 2
rpn: 72
status: "open"
assignee: "Burak Öz (Kıdemli Backend Geliştirici)"
tracker: "Selin Arslan (Software Lead)"
tags:
  - diğer
  - postgresql
  - performance
  - api
  - 5why
yokoten_applied: false
created_at: "2026-07-23T22:18:02.480336+00:00"
closed_at: ""
created_by: "Kullanici"
---

# [[Problems/Mikroservis API Yanıt Süresinde 450ms Gecikme Spaykı|Mikroservis API Yanıt Süresinde 450ms Gecikme Spaykı]]

## 🔍 Problem Açıklaması
Ödeme ve sipariş onay mikroservisinde yoğun saatlerde (14:00 - 16:00) ortalama yanıt süresi 45ms'den 450ms'ye yükseliyor, zaman aşımı hataları oluşuyor.

## 👥 Atamalar & Tarihler
- **Sorumlu (Assignee):** Burak Öz (Kıdemli Backend Geliştirici)
- **Denetçi (Tracker):** Selin Arslan (Software Lead)
- **Açılış Tarihi:** 23.07.2026 22:18
- **Kapanış Tarihi:** Açık

## 🧠 Kök Neden (Root Cause)
Veritabanı bağlantı havuzunun (connection pool) max_connections=20 ile sınırlandırılmış olması ve indeks bulunmayan sipariş sorgusunun PostgreSQL üzerinde Sequential Scan yapması.

## 🎓 Alınan Dersler (Lessons Learned)
Kök Neden: Eksik veritabanı indeksi ve yetersiz bağlantı havuzu.
Düzeltici Eylemler: PostgreSQL indeksi oluşturuldu, Redis önbellekleme devreye alındı.
Sonuç: P99 yanıt süresi 450ms'den 22ms'ye düşürüldü.
Önleyici Öneriler: CI/CD boru hattına yavaş sorgu ve eksik indeks analiz aşaması eklendi.

## 📊 Risk Değerlendirmesi & FMEA
| Şiddet (S) | Olasılık (O) | Saptanabilirlik (D) | RPN |
| :---: | :---: | :---: | :---: |
| 6 | 6 | 2 | **72** |

### 📋 Kapatma Kontrol Listesi
- [x] checklist


## 🛠️ Düzeltici Eylemler & Aksiyonlar
- [[Tasks/Aksiyon- Mikroservis API Yanıt Süresinde 450ms Gecikme|Aksiyon: Mikroservis API Yanıt Süresinde 450ms Gecikme]] — Sorumlu: **Burak Öz (Kıdemli Backend Geliştirici)** — Durum: `in_progress`



## 💬 Çözüm Sohbeti & AI Önerileri
**Kullanıcı:** Bu problem için kök neden ve çözüm önerileriniz nelerdir?

**AI Çözüm Ajanı:** Probleminiz detaylı incelendi. Kök neden: Veritabanı bağlantı havuzunun (connection pool) max_connections=20 ile sınırlandırılmış olması ve indeks bulunmayan sipariş sorgusunun PostgreSQL üzerinde Sequential Scan yapması.
Planlanan eylemler: 1. `CREATE INDEX idx_orders_user_created ON orders(user_id, created_at DESC)` indeksi eklendi.
2. Bağlantı havuzu boyutu 50'ye çıkarıldı ve Redis önbellek katmanı eklendi.



## 🔗 Sistem Bağlantıları
- Departman: [[Departments/Bilgi İşlem|Bilgi İşlem]]
- Metodoloji: [[Methodologies/5why|5why Metodolojisi]]
- Yokoten Uygulandı mı: **Hayır**
