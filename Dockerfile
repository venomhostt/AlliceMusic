# Use stable official Python image
FROM python:3.10-slim

# Install system dependencies (ffmpeg + curl)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    npm \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of project
COPY . .

# Expose port (Heroku uses dynamic $PORT)
ENV PORT=5000

# Start command
CMD ["bash", "start"]
