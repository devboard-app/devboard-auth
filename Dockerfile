FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
# requirements.txt is UTF-16; convert to UTF-8 before pip reads it
RUN python -c "open('requirements_utf8.txt','w').write(open('requirements.txt','r',encoding='utf-16').read())" \
    && pip install --no-cache-dir -r requirements_utf8.txt \
    && rm requirements_utf8.txt

COPY alembic.ini .
COPY alembic/ alembic/
COPY app/ app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
