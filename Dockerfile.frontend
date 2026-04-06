FROM node:25-slim

WORKDIR /app/frontend

RUN apt-get update && apt-get install -y git curl \
    && rm -rf /var/lib/apt/lists/*

COPY app/frontend/package*.json ./
RUN npm install

# bind-mounted source will override image at /app/frontend during development
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]