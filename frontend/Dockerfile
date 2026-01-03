# syntax=docker/dockerfile:1
FROM node:20.11-alpine AS builder
WORKDIR /app
COPY package*.json ./
ENV NODE_OPTIONS="--max-old-space-size=512"
RUN npm ci
COPY . .
RUN npm run build

FROM node:20.11-alpine
WORKDIR /app
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000
ENV NODE_ENV=production
CMD ["npm", "start"]