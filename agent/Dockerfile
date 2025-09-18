FROM python:3.11-slim

WORKDIR /app

# Install ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create directories for state
RUN mkdir -p /state

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set working directory to where the app module is
WORKDIR /app

ENV PYTHONPATH=/app

CMD ["python", "-u", "-m", "app.main"]