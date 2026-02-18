FROM node:22-alpine

WORKDIR /app

# Install dependencies first (layer caching)
COPY package.json ./
RUN npm install --production

# Copy server and static assets
COPY server.js ./
COPY viz/ ./viz/
COPY data/ ./data/

EXPOSE 3000

CMD ["node", "server.js"]
