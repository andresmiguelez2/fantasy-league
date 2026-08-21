FROM node:25-slim

WORKDIR /workspace/frontend

RUN apt-get update && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

COPY frontend/package*.json ./
RUN npm install

# bind-mounted source will override image at /workspace/frontend during development;
# the named volume frontend_node_modules shadows image deps, so re-sync on every
# start or new package.json dependencies are never picked up after a rebuild
CMD ["sh", "-c", "npm install --no-audit --no-fund && exec npm run dev -- --host 0.0.0.0 --port 8080"]