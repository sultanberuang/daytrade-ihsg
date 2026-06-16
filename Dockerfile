# Stage 1: Build React frontend
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python API + static files
FROM python:3.12-slim
WORKDIR /app/backend

RUN useradd -m -u 1000 user

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY --from=frontend /app/frontend/dist ./static
RUN chown -R user:user /app/backend

USER user
ENV HOME=/home/user PORT=7860
EXPOSE 7860

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
