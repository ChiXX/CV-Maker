#!/bin/bash

# CV-Maker 自动部署脚本
# 适用于Oracle Cloud VM.Standard.E2.1.Micro

set -e

echo "🚀 开始部署 CV-Maker 到 Oracle Cloud"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${GREEN}[步骤 $1]${NC} $2"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
   print_error "请不要使用root用户运行此脚本"
   exit 1
fi

print_step "1" "更新系统包"
sudo apt update && sudo apt upgrade -y

print_step "2" "安装Docker和Docker Compose"
# 安装Docker
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 添加用户到docker组
sudo usermod -aG docker $USER

print_step "3" "安装Git"
sudo apt install -y git

print_step "4" "克隆项目代码"
if [ ! -d "CV-Maker" ]; then
    git clone git@github.com:ChiXX/CV-Maker.git
fi
cd CV-Maker

print_step "5" "配置环境变量"
if [ ! -f ".env" ]; then
    cp env.example .env
    print_warning "请编辑 .env 文件配置以下变量:"
    print_warning "- OPENAI_API_KEY"
    print_warning "- OPENAI_BASE_URL (可选)"
    print_warning "- OPENAI_MODEL (可选)"
    print_warning "- NAME"
    echo "按回车键继续配置..."
    read
    nano .env
fi

print_step "6" "构建和启动服务"
# 停止可能存在的旧服务
docker-compose -f docker-compose.lightweight.yml down || true

# 启动服务
docker-compose -f docker-compose.lightweight.yml up -d --build

print_step "7" "等待服务启动"
echo "等待30秒让服务完全启动..."
sleep 30

print_step "8" "初始化数据库"
docker-compose -f docker-compose.lightweight.yml exec -T api python init_db.py

print_step "9" "检查服务状态"
docker-compose -f docker-compose.lightweight.yml ps

print_step "10" "验证部署"
# 检查API健康状态
if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
    print_step "✓" "API服务运行正常"
else
    print_error "API服务可能有问题，请检查日志"
fi

# 检查数据库连接
if docker-compose -f docker-compose.lightweight.yml exec -T postgres pg_isready -U cv_user -d cv_maker > /dev/null 2>&1; then
    print_step "✓" "数据库连接正常"
else
    print_error "数据库连接有问题"
fi

echo ""
echo "🎉 部署完成！"
echo ""
echo "📋 服务信息:"
echo "- API地址: http://$(curl -s ifconfig.me):8000"
echo "- API文档: http://$(curl -s ifconfig.me):8000/docs"
echo "- 数据库端口: 5432"
echo ""
echo "🔧 管理命令:"
echo "- 查看日志: docker-compose -f docker-compose.lightweight.yml logs -f"
echo "- 重启服务: docker-compose -f docker-compose.lightweight.yml restart"
echo "- 停止服务: docker-compose -f docker-compose.lightweight.yml down"
echo ""
echo "⚠️  重要提醒:"
echo "- 请确保安全组配置允许端口8000和5432的访问"
echo "- 定期备份数据库数据"
echo "- 监控内存使用情况"

print_warning "请重新连接SSH会话以使用docker命令（用户组变更需要重新登录）"
