FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# 后端依赖
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install -r ./backend/requirements.txt

# 源码 + 已构建的前端产物
COPY backend/ ./backend/
COPY frontend/dist/ ./frontend/dist/

# 魔搭创空间要求监听 7860 端口
EXPOSE 7860
CMD ["sh", "-c", "cd backend && gunicorn -w 1 --threads 4 --timeout 240 -b 0.0.0.0:${PORT:-7860} app:app"]
