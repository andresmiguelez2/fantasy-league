FROM python:3.13.9-slim

# Install Git and other development tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Keep container running for development
CMD ["tail", "-f", "/dev/null"]
