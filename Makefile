# 变量定义
DOCKER_IMAGE_NAME = fuel-price-tracker
DOCKER_CONTAINER_NAME = fuel-tracker
PORT = 5001

# 定义变量
COMPOSE = docker compose

# 默认目标
.PHONY: all
all: up

# 构建并启动所有服务
.PHONY: up
up:
	$(COMPOSE) up -d

# 停止并移除所有容器
.PHONY: down
down:
	$(COMPOSE) down

# 重新构建并启动所有服务
.PHONY: rebuild
rebuild:
	$(COMPOSE) up -d --build

# 查看服务日志
.PHONY: logs
logs:
	$(COMPOSE) logs -f

# 进入app容器的shell
.PHONY: shell
shell:
	$(COMPOSE) exec app /bin/bash

# 显示所有运行中的容器
.PHONY: ps
ps:
	$(COMPOSE) ps

# 停止所有服务
.PHONY: stop
stop:
	$(COMPOSE) stop

# 启动所有服务
.PHONY: start
start:
	$(COMPOSE) start

# 重启所有服务
.PHONY: restart
restart:
	$(COMPOSE) restart

# 清理未使用的镜像和卷
.PHONY: clean
clean:
	docker system prune -f
	docker volume prune -f

# 检查数据库
.PHONY: check-db
check-db:
	$(COMPOSE) up -d app  # 确保 app 服务正在运行
	$(COMPOSE) exec -T app python -c "from api import clean_database; clean_database()"

# 更新燃料价格并发送提醒邮件
.PHONY: update-and-notify
update-and-notify:
	$(COMPOSE) up -d app  # 确保 app 服务正在运行
	$(COMPOSE) exec -T app python -c "from api import update_fuel_prices_and_notify; update_fuel_prices_and_notify()"

# 帮助信息
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  up        - Build and start all services"
	@echo "  down      - Stop and remove all containers"
	@echo "  rebuild   - Rebuild and start all services"
	@echo "  logs      - View service logs"
	@echo "  shell     - Enter app container shell"
	@echo "  ps        - List running containers"
	@echo "  stop      - Stop all services"
	@echo "  start     - Start all services"
	@echo "  restart   - Restart all services"
	@echo "  clean     - Remove unused images and volumes"
	@echo "  check-db  - Check the database status"
	@echo "  update-and-notify - Update fuel prices and send notifications"
	@echo "  help      - Show this help message"