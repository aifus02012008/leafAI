# -*- coding: utf-8 -*-
"""
Deploy LEAF_AI Frontend SPA to Hugging Face Static Space
Repo: Hphuccoder28/leaf-ai-app
"""

import os
import sys
import logging
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from huggingface_hub import HfApi

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("deploy_space")

HF_TOKEN = "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"
SPACE_ID = "Hphuccoder28/leaf-ai-app"
FRONTEND_DIR = Path("d:/LEAF_AI/leafAI/frontend")

def deploy():
    api = HfApi(token=HF_TOKEN)
    logger.info(f"Đang kiểm tra Space {SPACE_ID}...")
    api.create_repo(repo_id=SPACE_ID, repo_type="space", space_sdk="static", exist_ok=True, private=False)
    
    logger.info(f"Đang tải toàn bộ thư mục frontend ({FRONTEND_DIR}) lên Hugging Face Space...")
    api.upload_folder(
        folder_path=str(FRONTEND_DIR),
        repo_id=SPACE_ID,
        repo_type="space",
        commit_message="Deploy LEAF_AI Botanical Recruiter & Diagnostic SPA"
    )
    logger.info(f"🎉 TRIỂN KHAI THÀNH CÔNG LÊN HUGGING FACE SPACE!")
    logger.info(f"👉 Space URL: https://huggingface.co/spaces/{SPACE_ID}")
    logger.info(f"👉 Direct App URL: https://hphuccoder28-leaf-ai-app.hf.space")

if __name__ == "__main__":
    deploy()
