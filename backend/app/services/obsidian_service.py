import os
import re
import uuid
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.models import ProblemRecordORM, Task

logger = logging.getLogger(__name__)

class ObsidianService:
    """Service to export PKM database records into a visual Obsidian Markdown Vault."""

    def __init__(self, db: AsyncSession, rag_service: Optional[Any] = None):
        self._db = db
        self._rag = rag_service
        # Vault path relative to the backend project root
        self.vault_path = Path("obsidian_vault")

    def _sanitize_filename(self, name: str) -> str:
        if not name:
            return "isimsiz_kayit"
        clean = re.sub(r'[<>:"/\\|?*]', "-", name)
        clean = re.sub(r'\s+', " ", clean)
        clean = re.sub(r'-+', "-", clean)
        return clean.strip()[:100]

    def init_vault(self):
        for folder in ["", "Problems", "Departments", "Methodologies", "Tasks", "Tags", ".obsidian"]:
            Path(self.vault_path / folder).mkdir(parents=True, exist_ok=True)

        graph_config = {
          "collapse-filter": False,
          "search": "",
          "showTags": True,
          "showAttachments": False,
          "hideUnresolved": False,
          "showOrphans": True,
          "collapse-color-groups": False,
          "colorGroups": [
            {"query": "path:Problems", "color": {"a": 1, "rgb": 14717183}},
            {"query": "path:Departments", "color": {"a": 1, "rgb": 5831512}},
            {"query": "path:Methodologies", "color": {"a": 1, "rgb": 3828351}},
            {"query": "path:Tasks", "color": {"a": 1, "rgb": 15024220}},
            {"query": "path:Tags", "color": {"a": 1, "rgb": 10243550}}
          ],
          "collapse-display": False,
          "showArrow": True,
          "textFadeMultiplier": 0.0,
          "nodeSizeMultiplier": 1.5,
          "lineThicknessMultiplier": 1.2,
          "forceMultiplier": 1.0,
          "linkDistanceMultiplier": 1.0,
          "centerStrength": 0.5,
          "repelStrength": 12.0
        }
        
        graph_file = self.vault_path / ".obsidian" / "graph.json"
        if not graph_file.exists():
            with open(graph_file, "w", encoding="utf-8") as f:
                json.dump(graph_config, f, indent=2, ensure_ascii=False)

        app_config = {
            "showLineNumber": True,
            "useMarkdownLinks": False,
            "showUnsupportedFiles": False,
            "promptOnDelete": False
        }
        app_file = self.vault_path / ".obsidian" / "app.json"
        if not app_file.exists():
            with open(app_file, "w", encoding="utf-8") as f:
                json.dump(app_config, f, indent=2, ensure_ascii=False)

        self._write_methodology_templates()

    def _write_methodology_templates(self):
        methodologies = {
            "8D": "# 8D Methodology (8 Disiplin)\n\nEndüstriyel süreçlerde ortaya çıkan ürün ve süreç problemlerinin kök nedenlerini belirleme, geçici ve kalıcı düzeltici eylemleri alma ve kapatma sürecini sistematik hale getiren metodolojidir.\n\n## Bu Metodolojiyi Kullanan Vakalar\n",
            "5-Why": "# 5-Why Methodology (5 Neden Analizi)\n\nProblemlerin yüzeydeki belirtilerinden derine inerek gerçek kök nedenleri bulmak amacıyla ardışık 'Neden?' sorularının sorulduğu basit ama etkili bir analiz yöntemidir.\n\n## Bu Metodolojiyi Kullanan Vakalar\n",
            "Ishikawa": "# Ishikawa (Kılçık Diyagramı)\n\nBir probleme etki edebilecek olası tüm nedenleri kategori bazında (İnsan, Makine, Metot, Malzeme, Ölçüm, Çevre) görselleştiren ve kök neden analizine zemin hazırlayan neden-sonuç diyagramıdır.\n\n## Bu Metodolojiyi Kullanan Vakalar\n",
            "PDCA": "# PDCA (PUKÖ Döngüsü)\n\nPlanla, Uygula, Kontrol Et, Önlem Al adımlarından oluşan, sürekli iyileştirmeyi (Kaizen) odağına alan yönetim döngüsüdür.\n\n## Bu Metodolojiyi Kullanan Vakalar\n",
            "AGENT": "# Yapay Zeka Danışman (AI Agent)\n\nDoğrudan AI Agent yönlendirmesiyle, serbest chat formatında gerçekleştirilen problem çözme seansıdır.\n\n## Bu Metodolojiyi Kullanan Vakalar\n"
        }

        for m_name, m_content in methodologies.items():
            m_file = self.vault_path / "Methodologies" / f"{m_name}.md"
            if not m_file.exists():
                with open(m_file, "w", encoding="utf-8") as f:
                    f.write(m_content)

    async def export_record(self, record_id: uuid.UUID) -> Optional[Path]:
        self.init_vault()

        # Load record with user
        result = await self._db.execute(
            select(ProblemRecordORM)
            .options(joinedload(ProblemRecordORM.user))
            .where(ProblemRecordORM.id == record_id)
        )
        record = result.scalar_one_or_none()
        if not record:
            return None

        # Load tasks
        tasks_result = await self._db.execute(
            select(Task).where(Task.problem_record_id == record_id)
        )
        tasks = list(tasks_result.scalars().all())

        created_by = record.user.full_name if record.user else "System User"
        
        # Sanitized filenames
        title_sanitized = self._sanitize_filename(record.title)
        dept_sanitized = self._sanitize_filename(record.department or "Diger")
        meth_sanitized = self._sanitize_filename(record.methodology or "Diger")

        # Query similar problems from Qdrant
        similar_links_markdown = ""
        if self._rag:
            try:
                # Query RAG
                query_text = f"{record.title} {record.description}"
                results = await self._rag.search(query_text)
                similar_cases = [r for r in results if str(r.get("id")) != str(record_id)]
                if similar_cases:
                    similar_links_markdown += "\n## 👥 Benzer Vakalar (Semantik RAG)\n"
                    for case in similar_cases:
                        similarity = int(case.get("score", 0.5) * 100)
                        case_title = case.get("title", "Bilinmeyen Başlık")
                        case_file_sanitized = self._sanitize_filename(case_title)
                        similar_links_markdown += f"- [[Problems/{case_file_sanitized}|{case_title}]] (Benzerlik Skoru: %{similarity})\n"
            except Exception as e:
                logger.error(f"Obsidian sync similarity match error: {e}")

        # Format FMEA Metrics
        fmea_text = f"| Şiddet (S) | Olasılık (O) | Saptanabilirlik (D) | RPN |\n| :---: | :---: | :---: | :---: |\n| {record.severity or 1} | {record.occurrence or 1} | {record.detection or 1} | **{record.rpn or 1}** |\n"

        # Format Closure Checklist
        checklist_text = ""
        if record.closure_checklist:
            checklist_text = "### 📋 Kapatma Kontrol Listesi\n"
            for item, checked in record.closure_checklist.items():
                status_box = "[x]" if checked else "[ ]"
                checklist_text += f"- {status_box} {item}\n"

        # Tasks links and files
        tasks_text = ""
        if tasks:
            tasks_text = "\n## 🛠️ Düzeltici Eylemler & Aksiyonlar\n"
            for t in tasks:
                task_filename = self._sanitize_filename(t.title)
                tasks_text += f"- [[Tasks/{task_filename}|{t.title}]] — Sorumlu: **{t.assignee_name or 'Atanmamış'}** — Durum: `{t.status}`\n"
                await self._export_task(t, title_sanitized)

        # Build YAML frontmatter
        tags_list = record.tags or []
        if record.problem_category:
            tags_list.append(record.problem_category.lower())
        tags_list = list(set(tags_list)) # deduplicate

        escaped_title = record.title.replace('"', '\\"')
        formatted_tags = "\n".join([f"  - {tag}" for tag in tags_list])

        frontmatter = f"""---
id: {str(record.id)}
title: "{escaped_title}"
department: "{record.department or 'Diğer'}"
methodology: "{record.methodology}"
severity: {record.severity or 1}
occurrence: {record.occurrence or 1}
detection: {record.detection or 1}
rpn: {record.rpn or 1}
status: "{record.resolution_status}"
tags:
{formatted_tags}
yokoten_applied: {str(record.yokoten_applied).lower()}
created_at: "{record.created_at.isoformat()}"
created_by: "{created_by}"
---

# [[Problems/{title_sanitized}|{record.title}]]

## 🔍 Problem Açıklaması
{record.description}

## 🧠 Kök Neden (Root Cause)
{record.root_cause}

## 🎓 Alınan Dersler (Lessons Learned)
{record.lessons_learned}

## 📊 Risk Değerlendirmesi & FMEA
{fmea_text}
{checklist_text}
{tasks_text}
{similar_links_markdown}
## 🔗 Sistem Bağlantıları
- Departman: [[Departments/{dept_sanitized}|{record.department or 'Diğer'}]]
- Metodoloji: [[Methodologies/{meth_sanitized}|{record.methodology} Metodolojisi]]
- Yokoten Uygulandı mı: **{"Evet" if record.yokoten_applied else "Hayır"}**
"""

        # Write Problem Note
        file_path = self.vault_path / "Problems" / f"{title_sanitized}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter)

        # Ensure index references updated
        self._update_department_note(record.department or "Diğer", record.title, title_sanitized)
        self._update_methodology_note(record.methodology, record.title, title_sanitized)
        for tag in tags_list:
            self._update_tag_note(tag, record.title, title_sanitized)

        return file_path

    async def _export_task(self, task: Task, parent_problem_filename: str):
        task_filename = self._sanitize_filename(task.title)
        task_file = self.vault_path / "Tasks" / f"{task_filename}.md"
        
        escaped_task_title = task.title.replace('"', '\\"')
        
        frontmatter = f"""---
id: {str(task.id)}
title: "{escaped_task_title}"
status: "{task.status}"
assignee: "{task.assignee_name or 'Atanmamış'}"
deadline: "{task.deadline.isoformat() if task.deadline else ''}"
created_at: "{task.created_at.isoformat()}"
---

# [[Tasks/{task_filename}|{task.title}]]

- **İlgili Problem:** [[Problems/{parent_problem_filename}|Probleme Git]]
- **Sorumlu:** {task.assignee_name or 'Atanmamış'}
- **Bitiş Tarihi:** {task.deadline.strftime('%d.%m.%Y') if task.deadline else 'Belirtilmedi'}
- **Durum:** `{task.status.upper()}`

## 📝 Aksiyon Açıklaması
{task.description or 'Açıklama belirtilmedi.'}

## 🔍 Kanıt & Doğrulama
Durum Kanıtı: {task.proof_description or 'Kanıt sunulmadı.'}
Kanıt Belgesi/URL: {task.proof_url or 'Ekli dosya yok.'}
"""
        with open(task_file, "w", encoding="utf-8") as f:
            f.write(frontmatter)

    def _update_department_note(self, dept_name: str, problem_title: str, problem_filename: str):
        dept_sanitized = self._sanitize_filename(dept_name)
        dept_file = self.vault_path / "Departments" / f"{dept_sanitized}.md"
        
        content = f"# {dept_name} Departmanı\n\nBu departmana ait çözülmüş problemler ve öğrenilen dersler.\n\n## Vakalar\n"
        
        if dept_file.exists():
            with open(dept_file, "r", encoding="utf-8") as f:
                existing = f.read()
            link = f"[[Problems/{problem_filename}|{problem_title}]]"
            if link in existing:
                return
            content = existing
        
        content += f"- [[Problems/{problem_filename}|{problem_title}]]\n"
        with open(dept_file, "w", encoding="utf-8") as f:
            f.write(content)

    def _update_methodology_note(self, meth_name: str, problem_title: str, problem_filename: str):
        meth_sanitized = self._sanitize_filename(meth_name)
        meth_file = self.vault_path / "Methodologies" / f"{meth_sanitized}.md"
        
        if not meth_file.exists():
            content = f"# {meth_name} Metodolojisi\n\n## Bu Metodolojiyi Kullanan Vakalar\n"
        else:
            with open(meth_file, "r", encoding="utf-8") as f:
                content = f.read()

        link = f"[[Problems/{problem_filename}|{problem_title}]]"
        if link in content:
            return

        content += f"- [[Problems/{problem_filename}|{problem_title}]]\n"
        with open(meth_file, "w", encoding="utf-8") as f:
            f.write(content)

    def _update_tag_note(self, tag_name: str, problem_title: str, problem_filename: str):
        tag_sanitized = self._sanitize_filename(tag_name)
        tag_file = self.vault_path / "Tags" / f"{tag_sanitized}.md"
        
        content = f"# #{tag_name} Etiketi\n\nBu etiketle ilişkilendirilmiş problem kayıtları.\n\n## Problemler\n"
        
        if tag_file.exists():
            with open(tag_file, "r", encoding="utf-8") as f:
                existing = f.read()
            link = f"[[Problems/{problem_filename}|{problem_title}]]"
            if link in existing:
                return
            content = existing
            
        content += f"- [[Problems/{problem_filename}|{problem_title}]]\n"
        with open(tag_file, "w", encoding="utf-8") as f:
            f.write(content)

    async def sync_all_records(self):
        """Clean vault and export all ProblemRecords from PostgreSQL to generate a fresh dashboard."""
        self.init_vault()
        
        # Clear existing Markdown files
        for folder in ["Problems", "Tasks", "Departments", "Tags"]:
            for item in Path(self.vault_path / folder).glob("*.md"):
                try:
                    item.unlink()
                except Exception:
                    pass

        self._write_methodology_templates()

        # Query all records
        db_records_result = await self._db.execute(
            select(ProblemRecordORM).options(joinedload(ProblemRecordORM.user))
        )
        db_records = list(db_records_result.scalars().all())
        
        total = len(db_records)
        rpn_sum = 0
        yokoten_count = 0
        rpn_high_count = 0
        
        recent_problems = []

        for record in db_records:
            await self.export_record(record.id)
            rpn_sum += (record.rpn or 1)
            if record.yokoten_applied:
                yokoten_count += 1
            if (record.rpn or 1) >= 120:
                rpn_high_count += 1
                
            recent_problems.append(record)

        # Sort recent problems by created_at desc
        recent_problems.sort(key=lambda x: x.created_at, reverse=True)
        recent_problems = recent_problems[:10]

        avg_rpn = int(rpn_sum / total) if total > 0 else 0
        
        dashboard_content = f"# 📊 Problem Bilgi Yönetim Paneli (PKM Dashboard)\n\n"
        dashboard_content += f"Hoş geldiniz! Burası kurumsal süreçlerde çözülen problemlerin, alınan derslerin ve düzeltici aksiyonların Obsidian üzerindeki merkezidir.\n\n"
        dashboard_content += f"## 📈 Genel Durum Göstergeleri\n"
        dashboard_content += f"- **Toplam Çözülen Problem:** {total}\n"
        dashboard_content += f"- **Ortalama Risk Skoru (RPN):** `{avg_rpn}`\n"
        dashboard_content += f"- **Yüksek Riskli Vaka Sayısı (RPN ≥ 120):** `{rpn_high_count}`\n"
        dashboard_content += f"- **Yokoten (Yatay Yayılım) Uygulanmış:** `{yokoten_count}` vaka\n\n"
        dashboard_content += f"---\n\n## ⚡ Son Eklenen Problem Kayıtları\n"
        
        for r in recent_problems:
            filename = self._sanitize_filename(r.title)
            dashboard_content += f"- [[Problems/{filename}|{r.title}]] — RPN: `{r.rpn or 1}` — Tarih: {r.created_at.strftime('%d.%m.%Y')} — Departman: [[Departments/{self._sanitize_filename(r.department or 'Diger')}|{r.department or 'Diğer'}]]\n"

        dashboard_content += """
---

## 📁 Bölümler & Yapılar
- **Metodolojiler:** 
  - [[Methodologies/8D|8D Analizleri]]
  - [[Methodologies/5-Why|5 Neden Analizleri]]
  - [[Methodologies/Ishikawa|Ishikawa Kılçık Diyagramları]]
  - [[Methodologies/PDCA|PUKÖ Döngüleri]]
  - [[Methodologies/AGENT|Yapay Zeka Danışman (AI Agent)]]
  
- **Sistem Departmanları:**
"""
        depts_dir = Path(self.vault_path / "Departments")
        for file in depts_dir.glob("*.md"):
            dept_name = file.stem.replace("-", " ")
            dashboard_content += f"  - [[Departments/{file.stem}|{dept_name.capitalize()}]]\n"

        dashboard_content += """
---
*İpucu: Tüm ağ yapısını görmek için sol menüden veya `Ctrl + G` kısayolu ile **Graph View** (İlişki Ağ Haritası) panelini açabilirsiniz.*
"""
        dashboard_file = self.vault_path / "Dashboard.md"
        with open(dashboard_file, "w", encoding="utf-8") as f:
            f.write(dashboard_content)
