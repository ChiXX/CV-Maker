#!/bin/bash

# 设置报错即停止
set -e

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

COMPOSE_FILE="docker-compose.lightweight.yml"

echo -e "${YELLOW}开始在低内存环境下部署项目...${NC}"

# 1. 确保已停止旧容器以释放内存
echo -e "${YELLOW}步骤 1: 停止现有服务以清理物理内存...${NC}"
sudo docker-compose -f $COMPOSE_FILE down --remove-orphans

# 2. 启动数据库（它是基础且占用极低）
echo -e "${YELLOW}步骤 2: 启动 Postgres 数据库...${NC}"
sudo docker-compose -f $COMPOSE_FILE up -d postgres

# 3. 清理系统缓存
echo -e "${YELLOW}步骤 3: 强制清理系统缓存 (drop_caches)...${NC}"
sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

# 4. 构建 API
echo -e "${YELLOW}步骤 4: 开始构建后端 API...${NC}"
sudo docker-compose -f $COMPOSE_FILE build api
echo -e "${GREEN}API 构建成功！${NC}"

# 5. 再次清理缓存，为前端构建做准备
echo -e "${YELLOW}步骤 5: 再次清理内存空间...${NC}"
sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

# 6. 构建前端（最吃内存的一步）
echo -e "${YELLOW}步骤 6: 开始构建前端 (Next.js)... 这可能需要较长时间，请耐心等待...${NC}"
# 使用 DOCKER_BUILDKIT=1 可以加速构建并减少冗余
sudo DOCKER_BUILDKIT=1 docker-compose -f $COMPOSE_FILE build frontend
echo -e "${GREEN}前端构建成功！${NC}"

# 7. 全力启动
echo -e "${YELLOW}步骤 7: 启动所有剩余服务...${NC}"
sudo docker-compose -f $COMPOSE_FILE up -d

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署成功！所有服务已在后台运行。${NC}"
echo -e "${GREEN}  API 地址: http://你的IP:2053${NC}"
echo -e "${GREEN}  前端地址: http://你的IP:80${NC}"
echo -e "${GREEN}========================================${NC}"

