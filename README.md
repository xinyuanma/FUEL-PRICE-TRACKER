# Fuel Price Tracker

Fuel Price Tracker 是一个用于监控和通知燃料价格变化的应用程序。它使用 Flask 构建，通过 Docker 进行部署，并使用 SQLite 数据库存储数据。

## 功能

- 自动抓取并存储芬兰 Oulu 地区的燃料价格信息
- 用户可以订阅价格提醒
- 当价格低于设定阈值时自动发送邮件通知
- 通过 Web 界面查看当前最新的燃料价格
- 使用 SQLite 浏览器查看和管理数据库内容
- 手动管理加油站位置信息
- 计算用户位置到加油站的距离和预估行驶时间

## 技术栈

- Python 3.9
- Flask
- SQLite
- Docker
- Docker Compose
- BeautifulSoup (用于网页抓取)
- APScheduler (用于定时任务)

## 安装和运行

1. 克隆仓库：
   ```
   git clone https://github.com/yourusername/fuel-price-tracker.git
   cd fuel-price-tracker
   ```

2. 确保已安装 Docker 和 Docker Compose。

3. 使用 Makefile 命令构建和运行应用：
   ```
   make up
   ```

   这将构建 Docker 镜像并启动所有服务。

4. 访问应用：
   - 主应用：http://localhost:5001
   - SQLite 浏览http://localhost:3000

## 使用 Makefile

项目包含一个 Makefile，简化了 Docker 操作。以下是可用的命令：

- `make up`: 构建并启动所有服务
- `make down`: 停止并移除所有容器
- `make rebuild`: 重新构建并启动所有服务
- `make logs`: 查看服务日志
- `make shell`: 进入 app 容器的 shell
- `make ps`: 显示所有运行中的容器
- `make stop`: 停止所有服务
- `make start`: 启动所有服务
- `make restart`: 重启所有服务
- `make clean`: 清理未使用的镜像和卷
- `make check-db`: 检查数据库状态和记录数
- `make update-and-notify`: 手动触发价格更新和通知发送
- `make help`: 显示帮助信息

## 配置

- 环境变量可以在 `docker-compose.yml` 文件中进行配置。
- 数据库文件 (`fuel_prices.db`) 存储在 `./data` 目录中。
- 邮件发送配置（SMTP 服务器、端口、用户名和密码）需要在 `docker-compose.yml` 文件中设置。

## 环境变量设置

在项目根目录创建一个 `.env` 文件，包含以下环境变量：

```
DATABASE_URL
```

## 数据更新和通知

- 应用程序每小时自动更新一次燃料价格。
- 当价格低于用户设定的阈值时，系统会自动发送邮件通知。
- 您也可以使用 `make update-and-notify` 命令手动触发更新和通知过程。

## 使用说明

- 在主页上，您可以输入您的邮箱地址和车辆所在地址来添加车辆位置。
- 添加车辆位置后，您可以查看到各个加油站的距离和预估行驶时间。
- 访问 `/manage_stations` 路由来手动添加或更新加油站的位置信息。

## 贡献

欢迎提交 Pull Requests。对于重大更改，请先开 issue 讨论您想要改变的内容。

## 许可证

[MIT](https://choosealicense.com/licenses/mit/)