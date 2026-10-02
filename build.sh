set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations (--fake-initial: an toàn nếu DB đã có bảng từ lần build trước)
python manage.py migrate --fake-initial
