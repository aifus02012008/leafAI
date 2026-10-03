#!/usr/bin/env python
"""Django's command-line utility for administrative tasks (delegates to backend/)."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks delegating to backend directory."""
    root = Path(__file__).resolve().parent
    backend_dir = root / 'backend'
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    os.chdir(backend_dir)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dermai.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Please use backend/.venv or run: "
            "backend\\.venv\\Scripts\\python.exe manage.py"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

