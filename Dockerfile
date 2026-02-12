# Use a lightweight Python version
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# 1. Install the OS libraries that OpenCV needs (This fixes the crash!)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy requirements and install
COPY requirements.txt .
# We install the standard libraries. The OS libs above make them work.
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the rest of the app code
COPY . .

# 4. Run the app
# (We use the array format to avoid shell issues)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]