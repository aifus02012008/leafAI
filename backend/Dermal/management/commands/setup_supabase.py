# -*- coding: utf-8 -*-
"""
Django Management Command: setup_supabase
Khởi tạo và đồng bộ dữ liệu nông nghiệp LEAF_AI (6 bệnh cà chua & Cẩm nang IPM)
vào cơ sở dữ liệu nội bộ SQLite và Supabase Cloud (nếu đã cấu hình).
"""

from django.core.management.base import BaseCommand
from Dermal.leaf_knowledge import TOMATO_DISEASES, FAO_IPM_HANDBOOK
from Dermal.models import TomatoDisease, IPMHandbookItem
from Dermal.supabase_client import is_supabase_configured, seed_supabase_knowledge_base, get_supabase_status


class Command(BaseCommand):
    help = "Khoi tao du lieu 6 benh ca chua & Cam nang IPM vao SQLite va dong bo len Supabase Cloud"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== KHOI TAO DU LIEU LEAF_AI & SUPABASE ==="))

        # 1. Seed vào Django SQLite
        diseases_created = 0
        for key, d in TOMATO_DISEASES.items():
            obj, created = TomatoDisease.objects.get_or_create(
                disease_id=key,
                defaults={
                    "name_en": d.get("name_en", key),
                    "name_vi": d.get("name_vi", key),
                    "pathogen": d.get("pathogen", ""),
                    "color": d.get("color", "#ea580c"),
                    "severity_default": d.get("severity", "Nghiêm trọng"),
                    "confidence_default": float(d.get("confidence", 50.0)),
                    "symptoms_stage1": d.get("symptoms", {}).get("stage_1", ""),
                    "symptoms_stage2": d.get("symptoms", {}).get("stage_2", ""),
                    "symptoms_stage3": d.get("symptoms", {}).get("stage_3", ""),
                    "conditions": d.get("conditions", ""),
                    "prevention": d.get("prevention", ""),
                    "treatment_cultural": d.get("treatment", {}).get("cultural", ""),
                    "treatment_bio": d.get("treatment", {}).get("biological", ""),
                    "treatment_chemical": d.get("treatment", {}).get("chemical", ""),
                    "references": d.get("references", "")
                }
            )
            if created:
                diseases_created += 1

        self.stdout.write(self.style.SUCCESS(f"[SQLite] Da tao moi {diseases_created} benh (Tong: {TomatoDisease.objects.count()} benh)."))

        # Seed Handbook
        handbook_created = 0
        if IPMHandbookItem.objects.count() == 0:
            for item in FAO_IPM_HANDBOOK.get("principles", []):
                IPMHandbookItem.objects.create(section="principles", step_num=item["num"], title=item["title"], description=item["desc"])
                handbook_created += 1
            for item in FAO_IPM_HANDBOOK.get("inspection", []):
                IPMHandbookItem.objects.create(section="inspection", step_num=item["step"], title=item["title"], description=item["desc"])
                handbook_created += 1
            for item in FAO_IPM_HANDBOOK.get("ipm", []):
                IPMHandbookItem.objects.create(section="ipm", step_num=item["step"], title=item["title"], description=item["desc"])
                handbook_created += 1
            for i, item in enumerate(FAO_IPM_HANDBOOK.get("safe_pesticide", [])):
                IPMHandbookItem.objects.create(section="safe", step_num=i + 1, title=item["rule"], description=item["desc"])
                handbook_created += 1

        self.stdout.write(self.style.SUCCESS(f"[SQLite] Da tao {handbook_created} muc Cam nang IPM (Tong: {IPMHandbookItem.objects.count()} muc)."))

        # 2. Kiểm tra & Seed Supabase Cloud
        status = get_supabase_status()
        self.stdout.write(f"Trang thai Supabase Cloud: {status['supabase_url']}")

        if status["configured"]:
            self.stdout.write(self.style.NOTICE("Dang day du lieu len Supabase Cloud..."))
            res = seed_supabase_knowledge_base()
            self.stdout.write(self.style.SUCCESS(f"[Supabase] Ket qua dong bo: {res}"))
        else:
            self.stdout.write(self.style.WARNING(
                "[Supabase] Chua cau hinh URL va API Key trong backend/.env.\n"
                "-> Ung dung dang hoat dong voi co so du lieu SQLite cuc bo.\n"
                "-> De dong bo len Supabase Cloud, vui long mo backend/.env va dien:\n"
                "   SUPABASE_URL=https://<your-project-id>.supabase.co\n"
                "   SUPABASE_KEY=<your-anon-or-service-role-key>\n"
            ))
