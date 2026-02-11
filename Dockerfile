# 1. Use a lightweight Python base image
FROM python:3.10-slim

# 2. Prevent Python from writing temporary files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Install system dependencies (Fixes the libGL/OpenCV error)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 4. Create a folder for the app
WORKDIR /app

# 5. Copy requirements and install Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application code
COPY . .

# 7. Open the port
EXPOSE 8000

# 8. Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]