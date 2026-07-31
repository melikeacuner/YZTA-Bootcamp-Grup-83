---
id: 2ec4fa97-9bd2-4542-a732-479223a6345f
title: "Enjeksiyon Kalıplama Plastik Parçada Çapak Kusuru"
department: "Kalite"
methodology: "ishikawa"
severity: 7
occurrence: 5
detection: 3
rpn: 105
status: "closed"
assignee: "Ahmet Yılmaz (Kalite Uzmanı)"
tracker: "Mehmet Demir (Üretim Müdürü)"
tags:
  - çapak
  - ishikawa
  - kalite hatası
  - fmea
  - enjeksiyon
  - plastik
yokoten_applied: true
created_at: "2026-07-23T22:18:00.701015+00:00"
closed_at: ""
created_by: "Kullanici"
---

# [[Problems/Enjeksiyon Kalıplama Plastik Parçada Çapak Kusuru|Enjeksiyon Kalıplama Plastik Parçada Çapak Kusuru]]

## 🔍 Problem Açıklaması
Otomotiv plastik parça üretim hattında 3 nolu enjeksiyon makinesinde kalıplanan parçalarda kenar çapaklanması ve boyut tolerans sapması gözlemlendi. Hata oranı %4.5 seviyesine çıktı.

## 👥 Atamalar & Tarihler
- **Sorumlu (Assignee):** Ahmet Yılmaz (Kalite Uzmanı)
- **Denetçi (Tracker):** Mehmet Demir (Üretim Müdürü)
- **Açılış Tarihi:** 23.07.2026 22:18
- **Kapanış Tarihi:** Açık

## 🧠 Kök Neden (Root Cause)
Kalıp kapama basıncının (clamping force) hidrolik valf aşınması nedeniyle 180 bardan 145 bara düşmesi ve eriyik sıcaklığının 230°C yerine 245°C çalıştırılması.

## 🎓 Alınan Dersler (Lessons Learned)
Kök Neden: Hidrolik valf basınç kaybı ve sıcaklık ayar sapması.
Düzeltici Eylemler: Valf değişimi, sıcaklık sensör kalibrasyonu ve parametre kilitleme yapıldı.
Sonuç: Çapak kusur oranı %4.5'ten %0.1'e düşürüldü.
Önleyici Öneriler: Periyodik hidrolik basınç denetimi 500 çalışma saatine indirildi.

## 📊 Risk Değerlendirmesi & FMEA
| Şiddet (S) | Olasılık (O) | Saptanabilirlik (D) | RPN |
| :---: | :---: | :---: | :---: |
| 7 | 5 | 3 | **105** |

### 📋 Kapatma Kontrol Listesi
- [x] checklist


## 🛠️ Düzeltici Eylemler & Aksiyonlar
- [[Tasks/Aksiyon- Enjeksiyon Kalıplama Plastik Parçada Çapak Ku|Aksiyon: Enjeksiyon Kalıplama Plastik Parçada Çapak Ku]] — Sorumlu: **Ahmet Yılmaz (Kalite Uzmanı)** — Durum: `completed`



## 💬 Çözüm Sohbeti & AI Önerileri
**Kullanıcı:** Bu problem için kök neden ve çözüm önerileriniz nelerdir?

**AI Çözüm Ajanı:** Probleminiz detaylı incelendi. Kök neden: Kalıp kapama basıncının (clamping force) hidrolik valf aşınması nedeniyle 180 bardan 145 bara düşmesi ve eriyik sıcaklığının 230°C yerine 245°C çalıştırılması.
Planlanan eylemler: 1. Hidrolik kapama valfi yenilendi ve sızdırmazlık contaları değiştirildi.
2. Kalıp sıcaklık kontrol cihazı kalibre edildi ve 225°C standart set değerine alındı.
3. Pres parametre kartı dijital kilit altına alındı.



## 🔗 Sistem Bağlantıları
- Departman: [[Departments/Kalite|Kalite]]
- Metodoloji: [[Methodologies/ishikawa|ishikawa Metodolojisi]]
- Yokoten Uygulandı mı: **Evet**
