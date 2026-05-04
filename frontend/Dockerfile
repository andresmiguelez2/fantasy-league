FROM node:25-slim

WORKDIR /workspace/frontend

RUN apt-get update && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

COPY frontend/package*.json ./
RUN npm install

# bind-mounted source will override image at /workspace/frontend during development
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "8080"]