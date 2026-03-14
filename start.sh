#!/bin/bash

# GTFS 项目启动脚本
# 用法: ./start.sh [start|stop|status]

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
BACKEND_PID_FILE="/tmp/gtfs_backend.pid"
FRONTEND_PID_FILE="/tmp/gtfs_frontend.pid"
BACKEND_LOG="/tmp/gtfs_backend.log"
FRONTEND_LOG="/tmp/gtfs_frontend.log"
BACKEND_PORT=5001
FRONTEND_PORT=5173

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

start() {
  echo -e "${YELLOW}启动 GTFS 项目...${NC}"

  # 检查 PostgreSQL
  if ! /opt/homebrew/opt/postgresql@16/bin/pg_isready -q 2>/dev/null; then
    echo -e "${YELLOW}PostgreSQL 未运行，正在启动...${NC}"
    brew services start postgresql@16
    sleep 2
  fi
  echo -e "${GREEN}✓ PostgreSQL 运行中${NC}"

  # 启动后端
  if [ -f "$BACKEND_PID_FILE" ] && kill -0 "$(cat $BACKEND_PID_FILE)" 2>/dev/null; then
    echo -e "${YELLOW}后端已在运行 (PID: $(cat $BACKEND_PID_FILE))${NC}"
  else
    cd "$BACKEND_DIR"
    PORT=$BACKEND_PORT python3 -m api.app > "$BACKEND_LOG" 2>&1 &
    echo $! > "$BACKEND_PID_FILE"
    sleep 2
    if curl -s "http://localhost:$BACKEND_PORT/api/health" > /dev/null 2>&1; then
      echo -e "${GREEN}✓ 后端启动成功 → http://localhost:$BACKEND_PORT${NC}"
    else
      echo -e "${RED}✗ 后端启动失败，查看日志: $BACKEND_LOG${NC}"
    fi
  fi

  # 启动前端
  if [ -f "$FRONTEND_PID_FILE" ] && kill -0 "$(cat $FRONTEND_PID_FILE)" 2>/dev/null; then
    echo -e "${YELLOW}前端已在运行 (PID: $(cat $FRONTEND_PID_FILE))${NC}"
  else
    cd "$FRONTEND_DIR"
    npm run dev > "$FRONTEND_LOG" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE"
    sleep 3
    if grep -q "Local:" "$FRONTEND_LOG" 2>/dev/null; then
      echo -e "${GREEN}✓ 前端启动成功 → http://localhost:$FRONTEND_PORT${NC}"
    else
      echo -e "${RED}✗ 前端启动失败，查看日志: $FRONTEND_LOG${NC}"
    fi
  fi

  echo ""
  echo -e "${GREEN}项目已启动:${NC}"
  echo -e "  前端: http://localhost:$FRONTEND_PORT"
  echo -e "  后端: http://localhost:$BACKEND_PORT"
  echo ""
  echo -e "${YELLOW}可选：启动准点率数据收集服务（需设置对应 API Key 环境变量）${NC}"
  echo -e "  SF_511_API_KEY=xxx python3 backend/scripts/start_punctuality_service.py --region sf &"
  echo -e "  MTA_API_KEY=xxx python3 backend/scripts/start_punctuality_service.py --region nyc &"
  echo -e "  TFNSW_API_KEY=xxx python3 backend/scripts/start_punctuality_service.py --region sydney &"
}

stop() {
  echo -e "${YELLOW}停止 GTFS 项目...${NC}"

  if [ -f "$BACKEND_PID_FILE" ]; then
    kill "$(cat $BACKEND_PID_FILE)" 2>/dev/null && echo -e "${GREEN}✓ 后端已停止${NC}"
    rm -f "$BACKEND_PID_FILE"
  else
    echo "后端未运行"
  fi

  if [ -f "$FRONTEND_PID_FILE" ]; then
    kill "$(cat $FRONTEND_PID_FILE)" 2>/dev/null && echo -e "${GREEN}✓ 前端已停止${NC}"
    rm -f "$FRONTEND_PID_FILE"
  else
    echo "前端未运行"
  fi
}

status() {
  echo -e "${YELLOW}GTFS 项目状态:${NC}"

  # PostgreSQL
  if /opt/homebrew/opt/postgresql@16/bin/pg_isready -q 2>/dev/null; then
    echo -e "  PostgreSQL: ${GREEN}运行中${NC}"
  else
    echo -e "  PostgreSQL: ${RED}未运行${NC}"
  fi

  # 后端
  if [ -f "$BACKEND_PID_FILE" ] && kill -0 "$(cat $BACKEND_PID_FILE)" 2>/dev/null; then
    echo -e "  后端 (PID: $(cat $BACKEND_PID_FILE)): ${GREEN}运行中${NC} → http://localhost:$BACKEND_PORT"
  else
    echo -e "  后端: ${RED}未运行${NC}"
  fi

  # 前端
  if [ -f "$FRONTEND_PID_FILE" ] && kill -0 "$(cat $FRONTEND_PID_FILE)" 2>/dev/null; then
    echo -e "  前端 (PID: $(cat $FRONTEND_PID_FILE)): ${GREEN}运行中${NC} → http://localhost:$FRONTEND_PORT"
  else
    echo -e "  前端: ${RED}未运行${NC}"
  fi
}

case "${1:-start}" in
  start)  start ;;
  stop)   stop ;;
  status) status ;;
  restart) stop; sleep 1; start ;;
  *)
    echo "用法: $0 [start|stop|status|restart]"
    exit 1
    ;;
esac
