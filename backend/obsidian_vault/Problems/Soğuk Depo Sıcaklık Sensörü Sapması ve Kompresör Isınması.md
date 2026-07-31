---
id: 12f29f5d-eaac-4d7c-944f-4323f7dfbc95
title: "Soğuk Depo Sıcaklık Sensörü Sapması ve Kompresör Isınması"
department: "Lojistik"
methodology: "8d"
severity: 8
occurrence: 3
detection: 4
rpn: 96
status: "closed"
assignee: "Fatma Şahin (Tesis Sorumlusu)"
tracker: "Caner Kaya (Operasyon Direktörü)"
tags:
  - lojistik gecikme
  - lojistik
  - fmea
  - 8d
  - sensör
  - soğuk-depo
yokoten_applied: true
created_at: "2026-07-23T22:18:01.794850+00:00"
closed_at: ""
created_by: "Kullanici"
---

# [[Problems/Soğuk Depo Sıcaklık Sensörü Sapması ve Kompresör Isınması|Soğuk Depo Sıcaklık Sensörü Sapması ve Kompresör Isınması]]

## 🔍 Problem Açıklaması
Gıda soğuk zincir lojistik deposunda B-4 alanında sıcaklık 4°C olması gerekirken 9.5°C'ye yükseldi. Alarm sistemi gecikmeli devreye girdi.

## 👥 Atamalar & Tarihler
- **Sorumlu (Assignee):** Fatma Şahin (Tesis Sorumlusu)
- **Denetçi (Tracker):** Caner Kaya (Operasyon Direktörü)
- **Açılış Tarihi:** 23.07.2026 22:18
- **Kapanış Tarihi:** Açık

## 🧠 Kök Neden (Root Cause)
PT100 sıcaklık sensör uçlarının nem korozyonuna uğrayarak direnç değerinin kayması ve kondanser fan filtrelerinin toz tıkaması nedeniyle kompresörün yüksek basınç korumasına geçmesi.

## 🎓 Alınan Dersler (Lessons Learned)
Kök Neden: Oksitlenen sensör ucu ve tıkalı kondanser filtresi.
Düzeltici Eylemler: IP68 sensör montajı ve SCADA alarm hassasiyet güncellemesi yapıldı.
Sonuç: Sıcaklık kararlılığı ±0.5°C aralığına getirildi.
Önleyici Öneriler: Tüm soğuk depolarda sensör kalibrasyonu 6 aylık periyoda çekildi.

## 📊 Risk Değerlendirmesi & FMEA
| Şiddet (S) | Olasılık (O) | Saptanabilirlik (D) | RPN |
| :---: | :---: | :---: | :---: |
| 8 | 3 | 4 | **96** |

### 📋 Kapatma Kontrol Listesi
- [x] checklist


## 🛠️ Düzeltici Eylemler & Aksiyonlar
- [[Tasks/Aksiyon- Soğuk Depo Sıcaklık Sensörü Sapması ve Kompre|Aksiyon: Soğuk Depo Sıcaklık Sensörü Sapması ve Kompre]] — Sorumlu: **Fatma Şahin (Tesis Sorumlusu)** — Durum: `completed`



## 💬 Çözüm Sohbeti & AI Önerileri
**Kullanıcı:** Bu problem için kök neden ve çözüm önerileriniz nelerdir?

**AI Çözüm Ajanı:** Probleminiz detaylı incelendi. Kök neden: PT100 sıcaklık sensör uçlarının nem korozyonuna uğrayarak direnç değerinin kayması ve kondanser fan filtrelerinin toz tıkaması nedeniyle kompresörün yüksek basınç korumasına geçmesi.
Planlanan eylemler: 1. IP68 korumalı paslanmaz kılıflı yeni PT100 sensör montajı yapıldı.
2. Kondanser fan filtreleri temizlendi ve otomatik basınçlı yıkama planına alındı.
3. SCADA alarm eşik değeri ±1°C hassasiyete çekildi.



## 🔗 Sistem Bağlantıları
- Departman: [[Departments/Lojistik|Lojistik]]
- Metodoloji: [[Methodologies/8d|8d Metodolojisi]]
- Yokoten Uygulandı mı: **Evet**
