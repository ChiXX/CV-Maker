# 🚀 Oracle Cloud 部署指南

## 📋 前置准备

### 1. Oracle Cloud 实例要求
- **实例类型**: VM.Standard.E2.1.Micro 或更高
- **操作系统**: Ubuntu 22.04
- **安全组配置**:
  - 允许 SSH (22端口)
  - 允许 HTTP (8000端口)
  - 允许 PostgreSQL (5432端口，可选)

### 2. 本地准备
- 项目代码已优化完成
- OpenAI API Key 已准备
- SSH 客户端已安装

---

## 📝 详细部署步骤

### 步骤1: 连接到Oracle Cloud实例

```bash
# 使用SSH连接 (替换为您的实例IP和密钥)
ssh -i your-private-key ubuntu@your-instance-ip
```

### 步骤2: 系统更新和依赖安装

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 安装Git
sudo apt install -y git

# 添加用户到docker组
sudo usermod -aG docker $USER
```

### 步骤3: 上传项目代码

**方法1: 使用Git (推荐)**
```bash
# 克隆项目 (使用SSH)
git clone git@github.com:ChiXX/CV-Maker.git
cd CV-Maker

# 如果代码在本地，压缩后上传
# 在本地:
# tar -czf cv-maker.tar.gz CV-Maker/
# scp cv-maker.tar.gz ubuntu@your-instance-ip:~/

# 在服务器解压:
# tar -xzf cv-maker.tar.gz
# cd CV-Maker
```

**方法2: 使用SCP上传**
```bash
# 从本地上传整个项目文件夹
scp -i your-private-key -r /path/to/CV-Maker ubuntu@your-instance-ip:~/
```

### 步骤4: 配置环境变量

```bash
cd CV-Maker

# 复制环境变量模板
cp env.example .env

# 编辑环境变量
nano .env
```

`.env` 文件内容:
```bash
OPENAI_API_KEY=your_actual_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=mistralai/mistral-small-3.1-24b-instruct:free
DATABASE_URL=postgresql://cv_user:cv_password@postgres:5432/cv_maker
NAME=Your Name
```

### 步骤5: 构建和启动服务

```bash
# 重新连接SSH会话（使用户组变更生效）
exit
ssh -i your-private-key ubuntu@your-instance-ip
cd CV-Maker

# 构建和启动轻量化服务
docker-compose -f docker-compose.lightweight.yml up -d --build

# 查看启动日志
docker-compose -f docker-compose.lightweight.yml logs -f
```

### 步骤6: 初始化数据库

```bash
# 等待服务完全启动（约30秒）
sleep 30

# 初始化数据库
docker-compose -f docker-compose.lightweight.yml exec api python init_db.py
```

### 步骤7: 验证部署

```bash
# 检查服务状态
docker-compose -f docker-compose.lightweight.yml ps

# 测试API健康状态
curl http://localhost:8000/docs

# 测试数据库连接
docker-compose -f docker-compose.lightweight.yml exec postgres pg_isready -U cv_user -d cv_maker

# 检查资源使用
docker stats
```

---

## 🔧 管理命令

### 查看服务状态
```bash
# 查看运行状态
docker-compose -f docker-compose.lightweight.yml ps

# 查看日志
docker-compose -f docker-compose.lightweight.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.lightweight.yml logs -f api
```

### 服务管理
```bash
# 重启所有服务
docker-compose -f docker-compose.lightweight.yml restart

# 重启特定服务
docker-compose -f docker-compose.lightweight.yml restart api

# 停止服务
docker-compose -f docker-compose.lightweight.yml down

# 停止并删除数据卷
docker-compose -f docker-compose.lightweight.yml down -v
```

### 更新部署
```bash
# 拉取最新代码
git pull origin main

# 重新构建和启动
docker-compose -f docker-compose.lightweight.yml up -d --build
```

---

## 🚨 故障排除

### 问题1: 内存不足
```bash
# 检查内存使用
free -h
docker stats

# 临时清理
docker system prune -a
sudo apt autoremove
```

### 问题2: 端口被占用
```bash
# 检查端口使用
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :5432

# 停止冲突服务或更改端口
```

### 问题3: Docker权限问题
```bash
# 确保用户在docker组中
groups $USER

# 如果不在组中，重新添加
sudo usermod -aG docker $USER
# 然后重新连接SSH
```

### 问题4: 数据库连接失败
```bash
# 检查数据库状态
docker-compose -f docker-compose.lightweight.yml logs postgres

# 重启数据库
docker-compose -f docker-compose.lightweight.yml restart postgres
```

### 问题5: API无法访问
```bash
# 检查API日志
docker-compose -f docker-compose.lightweight.yml logs api

# 测试本地访问
curl http://localhost:8000/docs

# 检查防火墙
sudo ufw status
```

---

## 📊 监控和维护

### 资源监控
```bash
# 系统资源
htop
free -h
df -h

# Docker资源
docker stats

# 应用日志
docker-compose -f docker-compose.lightweight.yml logs -f --tail=100
```

### 备份策略
```bash
# 数据库备份
docker-compose -f docker-compose.lightweight.yml exec postgres pg_dump -U cv_user cv_maker > backup_$(date +%Y%m%d_%H%M%S).sql

# 配置文件备份
cp .env .env.backup
```

### 日志轮转
```bash
# Docker日志轮转
docker-compose -f docker-compose.lightweight.yml logs --no-color > logs_$(date +%Y%m%d).txt
```

---

## 🌐 访问应用

部署完成后，您可以通过以下地址访问应用:

- **API地址**: `http://your-instance-ip:8000`
- **API文档**: `http://your-instance-ip:8000/docs`
- **数据库**: `postgresql://cv_user:cv_password@your-instance-ip:5432/cv_maker`

---

## ⚡ 快速部署脚本

如果您想使用自动化脚本:

```bash
# 上传部署脚本
scp deploy.sh ubuntu@your-instance-ip:~/

# 在服务器上运行
chmod +x deploy.sh
./deploy.sh
```

**注意**: 脚本需要根据您的实际情况修改Git仓库地址和配置。

---

## 📞 获取帮助

如果遇到问题，请按以下顺序检查:
1. 查看服务日志: `docker-compose -f docker-compose.lightweight.yml logs`
2. 检查系统资源: `free -h && df -h`
3. 验证环境变量: `cat .env`
4. 测试网络连接: `ping api.openai.com`

祝部署顺利！ 🎉
