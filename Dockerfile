# =============================================================================
# MiniStore — SQL Injection CTF Lab (ban rut gon: UNION / Boolean Blind / Auth Bypass)
# Dockerfile tuan thu guideline F-CTF:
#   - Chay voi USER 1000
#   - Root filesystem read-only, moi ghi du lieu dua vao /tmp (qua DB_PATH)
#   - Khong ghi file log ra dia — log ra stdout/stderr
#   - Chi expose DUY NHAT 1 port (8080)
#   - Khong dung capability dac biet, khong chay privileged
# =============================================================================
FROM python:3.12-alpine

RUN adduser -D -u 1000 appuser
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R 1000:1000 /app

USER 1000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TMPDIR=/tmp \
    DB_PATH=/tmp/store.db \
    PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "mkdir -p /tmp && python3 init_db.py && exec gunicorn app:app --bind 0.0.0.0:8080 --workers 2 --threads 4 --access-logfile - --error-logfile -"]
