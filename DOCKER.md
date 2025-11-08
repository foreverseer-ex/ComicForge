# Docker Compose 部署指南

## 前置要求

### 安装 Docker 和 Docker Compose

**Windows:**
1. 下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. 确保启用 WSL 2 后端（推荐）或 Hyper-V
3. Docker Desktop 已包含 Docker Compose，无需单独安装

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose-plugin

# 或者安装 Docker Compose V2（推荐）
sudo apt-get install docker-compose-plugin

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到 docker 组（避免每次使用 sudo）
sudo usermod -aG docker $USER
# 然后重新登录或执行：newgrp docker
```

**验证安装:**
```bash
# Windows (PowerShell/CMD) 或 Linux
docker --version
docker compose version
```

## 快速开始

### 1. 准备配置文件

确保项目根目录下有 `config.json` 文件。如果不存在，可以创建一个基本配置：

```json
{
  "llm": {
    "provider": "xai",
    "api_key": "your_api_key_here"
  }
}
```

### 2. 构建并启动服务

**Windows (PowerShell/CMD):**
```powershell
# 在项目根目录执行
docker compose up -d
```

**Linux:**
```bash
# 在项目根目录执行
docker compose up -d
```

**注意：** Windows 和 Linux 的命令完全相同！Docker Compose 是跨平台的。

### 3. 查看服务状态

```bash
# 查看所有服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
```

### 4. 访问应用

- **前端**: http://localhost:7863
- **后端 API**: http://localhost:7864
- **API 文档**: http://localhost:7864/docs

### 5. 停止服务

```bash
# 停止服务（保留容器）
docker compose stop

# 停止并删除容器（保留数据卷）
docker compose down

# 停止并删除容器和数据卷（⚠️ 会删除所有数据）
docker compose down -v
```

## 配置说明

### 环境变量

有两种方式设置环境变量：

#### 方式 1: 使用 `.env` 文件（推荐）

在项目根目录创建 `.env` 文件：

```env
# LLM API Keys
XAI_API_KEY=your_xai_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Civitai API Token
CIVITAI_API_TOKEN=your_civitai_token_here
```

然后在 `docker-compose.yml` 中取消注释相应的环境变量：

```yaml
environment:
  - XAI_API_KEY=${XAI_API_KEY}
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - CIVITAI_API_TOKEN=${CIVITAI_API_TOKEN}
```

#### 方式 2: 直接在 docker-compose.yml 中设置

```yaml
environment:
  - XAI_API_KEY=your_actual_api_key_here
  - OPENAI_API_KEY=your_actual_openai_key_here
  - CIVITAI_API_TOKEN=your_actual_token_here
```

**注意：** 方式 2 会将敏感信息暴露在配置文件中，不推荐用于生产环境。

### 数据持久化

- `./storage` 目录会挂载到容器中，确保数据持久化
- `./config.json` 配置文件会挂载到容器中（只读）

### 网络配置

- 前端和后端在同一个 Docker 网络中
- 前端通过 nginx 代理 `/api` 请求到后端
- 后端服务名称为 `backend`，前端可以通过 `http://backend:7864` 访问

## 开发模式

如果需要开发模式（热重载），可以修改 `docker-compose.yml`：

```yaml
backend:
  volumes:
    - ./src:/app/src  # 挂载源代码，支持热重载
```

## 常用命令

### 查看日志

```bash
# 查看所有服务日志
docker compose logs

# 查看特定服务日志
docker compose logs backend
docker compose logs frontend

# 实时跟踪日志（类似 tail -f）
docker compose logs -f

# 查看最近 100 行日志
docker compose logs --tail=100
```

### 重启服务

```bash
# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart backend
docker compose restart frontend
```

### 重新构建镜像

```bash
# 重新构建所有镜像（不使用缓存）
docker compose build --no-cache

# 重新构建特定服务
docker compose build --no-cache backend
docker compose build --no-cache frontend

# 构建并启动
docker compose up -d --build
```

### 进入容器调试

```bash
# 进入后端容器
docker compose exec backend bash

# 进入前端容器
docker compose exec frontend sh
```

## 故障排查

### 1. 端口被占用

**错误信息：** `Bind for 0.0.0.0:7863 failed: port is already allocated`

**解决方案：**
```bash
# Windows (PowerShell)
netstat -ano | findstr :7863
netstat -ano | findstr :7864

# Linux
sudo lsof -i :7863
sudo lsof -i :7864

# 或者修改 docker-compose.yml 中的端口映射
ports:
  - "8080:80"  # 前端改为 8080
  - "8081:7864"  # 后端改为 8081
```

### 2. 权限问题（Linux）

**错误信息：** `Permission denied` 或 `Cannot connect to the Docker daemon`

**解决方案：**
```bash
# 将用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker

# 如果仍有问题，检查 storage 目录权限
sudo chown -R $USER:$USER ./storage
chmod -R 755 ./storage
```

### 3. 构建失败

**检查点：**
- 确保网络连接正常（需要下载依赖）
- 检查 Docker 是否有足够的磁盘空间：`docker system df`
- 清理 Docker 缓存：`docker system prune -a`（⚠️ 会删除所有未使用的镜像）

### 4. 服务无法启动

```bash
# 查看详细错误信息
docker compose logs backend
docker compose logs frontend

# 检查容器状态
docker compose ps

# 检查健康状态
docker compose ps --format "table {{.Name}}\t{{.Status}}"
```

### 5. 数据丢失问题

确保 `storage` 目录已正确挂载：
```bash
# 检查挂载点
docker compose exec backend ls -la /app/storage

# 如果数据不在，检查 docker-compose.yml 中的 volumes 配置
```

### 6. 前端无法连接后端

```bash
# 检查网络连接
docker compose exec frontend ping backend

# 检查后端是否正常运行
curl http://localhost:7864/health

# 检查 nginx 配置
docker compose exec frontend cat /etc/nginx/conf.d/default.conf
```

## Windows 和 Linux 的区别

### 命令相同
Docker Compose 的命令在 Windows 和 Linux 上**完全相同**，都使用：
- `docker compose up -d` - 启动服务
- `docker compose down` - 停止服务
- `docker compose logs` - 查看日志
- 等等...

### 主要区别

1. **路径分隔符**
   - Windows: `C:\Users\...\ComicForge`
   - Linux: `/home/user/.../ComicForge`
   - **但在 docker-compose.yml 中，都使用 `/` 作为路径分隔符**

2. **权限管理**
   - Windows: 通常不需要特殊权限（如果使用 Docker Desktop）
   - Linux: 可能需要将用户添加到 `docker` 组，或使用 `sudo`

3. **文件权限**
   - Windows: 文件权限由 Windows 文件系统管理
   - Linux: 可能需要设置 `storage` 目录的权限：`chmod -R 755 ./storage`

4. **性能**
   - Windows (WSL 2): 性能接近原生 Linux
   - Windows (Hyper-V): 性能略低
   - Linux: 最佳性能

## 生产环境部署建议

1. **使用环境变量文件**: 创建 `.env` 文件管理敏感信息，不要提交到版本控制
2. **配置 HTTPS**: 使用 Nginx 反向代理配置 SSL 证书
3. **数据备份**: 定期备份 `./storage` 目录
4. **资源限制**: 在 `docker-compose.yml` 中添加资源限制：
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
   ```
5. **日志管理**: 配置日志轮转，避免日志文件过大
6. **监控**: 使用 Docker 健康检查或外部监控工具

## 注意事项

1. **端口冲突**: 确保 7863 和 7864 端口未被占用
2. **配置文件**: 确保 `config.json` 存在，否则会使用默认配置
3. **数据目录**: 确保 `storage` 目录存在且有写权限
4. **API Key**: 生产环境请使用环境变量或 secrets 管理敏感信息
5. **防火墙**: 确保防火墙允许访问 7863 和 7864 端口
6. **磁盘空间**: 确保有足够的磁盘空间存储镜像和数据

## 完整部署流程示例

```bash
# 1. 克隆或进入项目目录
cd ComicForge

# 2. 创建 .env 文件（可选，用于设置 API Keys）
echo "XAI_API_KEY=your_key_here" > .env

# 3. 确保配置文件存在
# （如果不存在，创建 config.json）

# 4. 构建并启动服务
docker compose up -d

# 5. 查看日志确认服务正常
docker compose logs -f

# 6. 访问应用
# 浏览器打开 http://localhost:7863
```

## 更新应用

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建并启动
docker compose up -d --build

# 3. 查看更新后的日志
docker compose logs -f
```


