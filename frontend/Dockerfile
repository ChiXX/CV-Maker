# syntax=docker/dockerfile:1
FROM node:20.11-alpine
WORKDIR /app
COPY package*.json ./
ENV NODE_OPTIONS="--max-old-space-size=512"

# Install all dependencies (including dev dependencies for development)
RUN npm ci --include=dev

# Copy source code
COPY . .

EXPOSE 3000

# Default to production, but can be overridden
ENV NODE_ENV=production
CMD ["npm", "start"]