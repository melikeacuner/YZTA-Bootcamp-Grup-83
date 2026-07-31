---
id: 1ddf4b0e-9130-4bb2-b4b5-e0ea22936581
title: "Sanal Sunucu VMware'den Nutanix AHV'ye Geçiş Sonrası Uygulama Erişim Başarısızlığı"
department: "Bilgi İşlem"
methodology: "5why"
severity: 7
occurrence: 4
detection: 3
rpn: 84
status: "closed"
assignee: "Ahmet Yılmaz (Kıdemli Bulut Mimar)"
tracker: "Deniz Er (IT Ops Manager)"
tags:
  - virtio
  - diğer
  - migration
  - vmware
  - cloud
  - nutanix
yokoten_applied: true
created_at: "2026-07-23T22:18:03.121453+00:00"
closed_at: ""
created_by: "Kullanici"
---

# [[Problems/Sanal Sunucu VMware'den Nutanix AHV'ye Geçiş Sonrası Uygulama Erişim Başarısızlığı|Sanal Sunucu VMware'den Nutanix AHV'ye Geçiş Sonrası Uygulama Erişim Başarısızlığı]]

## 🔍 Problem Açıklaması
Sanal sunucular VMware ESXi ortamından Nutanix AHV hipervizörüne taşındıktan sonra bazı sunucularda çalışan kritik uygulamalar başlamıyor ve ağ erişim hataları veriyor.

## 👥 Atamalar & Tarihler
- **Sorumlu (Assignee):** Ahmet Yılmaz (Kıdemli Bulut Mimar)
- **Denetçi (Tracker):** Deniz Er (IT Ops Manager)
- **Açılış Tarihi:** 23.07.2026 22:18
- **Kapanış Tarihi:** Açık

## 🧠 Kök Neden (Root Cause)
VMware vNIC ağ adaptörünün Nutanix VirtIO/VirtIO-Net sürücülerinin sanal sunucu imajına önceden yüklenmemiş olması ve vNIC UUID/MAC adres eşleşmeme sorunu.

## 🎓 Alınan Dersler (Lessons Learned)
Kök Neden: Eksik VirtIO sanallaştırma sürücüsü ve vNIC UUID uyuşmazlığı.
Düzeltici Eylemler: VirtIO paketleri yüklendi, sanal ağ kartı re-configure edildi.
Sonuç: Tüm iş uygulamaları Nutanix kümesinde kesintisiz çalışmaya başladı.
Önleyici Öneriler: Migrasyon checklist'ine geçiş öncesi VirtIO sürücü uyumluluk tarama adımı eklendi.

## 📊 Risk Değerlendirmesi & FMEA
| Şiddet (S) | Olasılık (O) | Saptanabilirlik (D) | RPN |
| :---: | :---: | :---: | :---: |
| 7 | 4 | 3 | **84** |

### 📋 Kapatma Kontrol Listesi
- [x] checklist


## 🛠️ Düzeltici Eylemler & Aksiyonlar
- [[Tasks/Aksiyon- Sanal Sunucu VMware'den Nutanix AHV'ye Geçiş|Aksiyon: Sanal Sunucu VMware'den Nutanix AHV'ye Geçiş ]] — Sorumlu: **Ahmet Yılmaz (Kıdemli Bulut Mimar)** — Durum: `completed`



## 💬 Çözüm Sohbeti & AI Önerileri
**Kullanıcı:** Bu problem için kök neden ve çözüm önerileriniz nelerdir?

**AI Çözüm Ajanı:** Probleminiz detaylı incelendi. Kök neden: VMware vNIC ağ adaptörünün Nutanix VirtIO/VirtIO-Net sürücülerinin sanal sunucu imajına önceden yüklenmemiş olması ve vNIC UUID/MAC adres eşleşmeme sorunu.
Planlanan eylemler: 1. Nutanix VirtIO-Win/VirtIO-Linux sürücü paketleri sanal makine imajında güncellendi.
2. vNIC adaptörü VirtIO-Net olarak yeniden yapılandırılıp static IP ve DNS eşleşmeleri doğrulandı.



## 🔗 Sistem Bağlantıları
- Departman: [[Departments/Bilgi İşlem|Bilgi İşlem]]
- Metodoloji: [[Methodologies/5why|5why Metodolojisi]]
- Yokoten Uygulandı mı: **Evet**
