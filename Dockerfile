# AI-Recruiter — контейнер для Streamlit-демо.
#
# Сборка и запуск:
#   docker build -t ai-recruiter .
#   docker run -p 8501:8501 ai-recruiter
#
# Внутри образа пайплайн работает в fallback-режиме (без torch/chromadb/LLM):
# хэшинг-эмбеддер + in-memory хранилище + rule-based агенты. Для реальных
# эмбеддингов и LLM подключите их отдельно.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Лёгкие зависимости (без тяжёлого ML-стека) + streamlit для демо.
COPY requirements.txt requirements-demo.txt ./
RUN pip install -r requirements.txt -r requirements-demo.txt

COPY . .

# Демо-данные генерируются при старте (фиксированный seed).
CMD ["sh", "-c", "python -m ai_recruiter.data.generator --n 100 && python -m ai_recruiter.data.vacancies && streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]
