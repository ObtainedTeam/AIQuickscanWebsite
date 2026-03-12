FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
# cache bust Thu Mar 12 11:47:11     2026
