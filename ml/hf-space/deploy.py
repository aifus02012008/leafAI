# -*- coding: utf-8 -*-
"""
LEAF_AI - One-Click Hugging Face Space Deployment Script
Tự động tạo Space trên Hugging Face và đẩy toàn bộ mã nguồn AI Server lên.
"""

import os
import sys
import argparse
from pathlib import Path

# Đảm bảo UTF-8 trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def deploy(token: str = None, space_name: str = "leaf-ai-tomato-engine"):
    try:
        from huggingface_hub import HfApi, login
    except ImportError:
        print("[INFO] Đang cài đặt huggingface_hub...")
        os.system(f"{sys.executable} -m pip install huggingface_hub")
        from huggingface_hub import HfApi, login

    # Lấy token từ đối số hoặc biến môi trường hoặc nhập trực tiếp
    hf_token = token or os.getenv("HF_TOKEN")
    if not hf_token:
        print("\n=======================================================")
        print("[AUTH] BẠN CẦN CUNG CẤP HUGGING FACE TOKEN (Write Permission)")
        print("Lấy token miễn phí tại: https://huggingface.co/settings/tokens")
        print("=======================================================\n")
        hf_token = input("Nhập Hugging Face Token của bạn: ").strip()

    if not hf_token:
        print("[ERROR] Chưa cung cấp Hugging Face Token.")
        sys.exit(1)

    api = HfApi(token=hf_token)

    try:
        user_info = api.whoami()
        username = user_info["name"]
        print(f"\n[OK] Đã xác thực tài khoản Hugging Face: {username}")
    except Exception as e:
        print(f"[ERROR] Token không hợp lệ hoặc đã hết hạn: {e}")
        sys.exit(1)

    repo_id = f"{username}/{space_name}"
    print(f"\n[DEPLOY] Đang tạo / kiểm tra Hugging Face Space: {repo_id}...")

    try:
        api.create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="docker",
            private=False,
            exist_ok=True
        )
        print(f"[OK] Space '{repo_id}' đã sẵn sàng trên Hugging Face!")
    except Exception as e:
        print(f"[NOTE] Lưu ý khi tạo repo: {e}")

    # Đẩy mã nguồn từ thư mục hf_space_leaf_ai lên Space
    current_dir = Path(__file__).resolve().parent
    print(f"[UPLOAD] Đang tải các tệp từ {current_dir} lên Space...")

    try:
        api.upload_folder(
            folder_path=str(current_dir),
            repo_id=repo_id,
            repo_type="space",
            ignore_patterns=["deploy.py", "__pycache__/*", "*.pyc"]
        )
        print("[SUCCESS] TAI LEN THANH CONG 100%!")
    except Exception as e:
        print(f"[ERROR] Loi khi tai tep len: {e}")
        sys.exit(1)

    # Tính toán URL chuẩn của Space
    clean_subdomain = f"{username}-{space_name}".replace("_", "-").lower()
    space_api_url = f"https://{clean_subdomain}.hf.space/predict_with_gradcam"

    print("\n" + "=" * 60)
    print("[INFO] THONG TIN SPACE VU TAO:")
    print(f"* Duong dan Space: https://huggingface.co/spaces/{repo_id}")
    print(f"* Endpoint API:   {space_api_url}")
    print("=" * 60)

    # Tự động cập nhật file backend/.env
    backend_env = current_dir.parent / "backend" / ".env"
    if backend_env.exists():
        content = backend_env.read_text(encoding="utf-8")
        if "AI_SERVER_URL=" in content:
            lines = []
            for line in content.splitlines():
                if line.startswith("AI_SERVER_URL="):
                    lines.append(f"AI_SERVER_URL={space_api_url}")
                else:
                    lines.append(line)
            backend_env.write_text("\n".join(lines), encoding="utf-8")
            print(f"[OK] Da cap nhat AI_SERVER_URL trong {backend_env}!")
        else:
            with open(backend_env, "a", encoding="utf-8") as f:
                f.write(f"\nAI_SERVER_URL={space_api_url}\n")
            print(f"[OK] Da them AI_SERVER_URL vao {backend_env}!")

    print("\n[NOTE] Space se mat khoang 1-2 phut de build Docker tren Hugging Face.")
    print("Sau khi build xong, backend Django se ket noi toi AI server moi nay!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy to Hugging Face Space")
    parser.add_argument("--token", type=str, help="Hugging Face Token (Write)")
    parser.add_argument("--space-name", type=str, default="leaf-ai-tomato-engine", help="Tên Space trên Hugging Face")
    args = parser.parse_args()

    deploy(token=args.token, space_name=args.space_name)
