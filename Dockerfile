FROM python:3.10-slim

# Install system dependencies for OpenCV and standard libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Environment variable placeholders
ENV ROBOFLOW_API_KEY=""

ENTRYPOINT ["python", "predict.py"]
