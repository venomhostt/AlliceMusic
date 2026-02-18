FROM python:3.10-slim

# Install required system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    nodejs \
    npm \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5000

CMD ["bash", "start"]
