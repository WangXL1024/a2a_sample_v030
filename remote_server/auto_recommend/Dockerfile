# 使用官方 Python 镜像
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制整个项目
COPY . .

# 设置环境变量（可选）
ENV PYTHONPATH=/app

# 启动命令：直接运行根目录的 __main__.py
CMD ["python", "__main__.py"]