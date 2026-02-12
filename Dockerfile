# Use Python 3.10 Slim (Lightweight)
FROM python:3.10-slim

WORKDIR /app

# 1. Install the missing Graphics Libraries (Fixes cv2 error)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the app code
COPY . .

# 4. Command to run the app
CMD ["python", "main.py"]