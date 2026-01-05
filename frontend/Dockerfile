# syntax=docker/dockerfile:1
FROM node:20.11-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
ENV NEXT_TELEMETRY_DISABLED 1


FROM base AS development
COPY . .
EXPOSE 3000
CMD ["npm", "run dev"]

FROM base AS builder
COPY . .
# 针对 Oracle 1G 内存的限制
ENV NODE_OPTIONS="--max-old-space-size=1024"
RUN npm run build

FROM node:20.11-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_OPTIONS="--max-old-space-size=512"

# 只拷贝生产环境必需的文件
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000
CMD ["npm", "start"]