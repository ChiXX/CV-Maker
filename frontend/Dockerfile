# syntax=docker/dockerfile:1

# 1. 基础阶段 (我们将其命名为 base)
FROM node:20.11-alpine AS base
WORKDIR /app
# 禁用匿名遥测
ENV NEXT_TELEMETRY_DISABLED 1
COPY package*.json ./
# 安装所有依赖（开发+生产）
RUN npm install

# 2. 开发阶段 (development)
# 本地开发时，docker-compose 会使用 target: development
FROM base AS development
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# 3. 构建阶段 (builder)
# 专门用于在 Oracle 上进行重量级的 Next.js 编译
FROM base AS builder
# --- ADD THESE LINES ---
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
# -----------------------

COPY . .
ENV NODE_OPTIONS="--max-old-space-size=1024"
RUN npm run build

# 4. 运行阶段 (runner)
# 最终运行在 Oracle 上的轻量化镜像
FROM node:20.11-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED 1
# 运行时的内存限制，512M 足够
ENV NODE_OPTIONS="--max-old-space-size=512"

# 仅从 builder 阶段拷贝生成的产物，不拷贝源码，镜像体积骤减
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000
CMD ["npm", "start"]