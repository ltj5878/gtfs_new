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
}

stop() {
  echo -e "${YELLOW}停止 GTFS 项目...${NC}"

  # 停止后端：先尝试 PID 文件，再按端口兜底
  local backend_stopped=false
  if [ -f "$BACKEND_PID_FILE" ]; then
    local pid=$(cat "$BACKEND_PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null
      sleep 1
      # 如果还没死，强制杀
      kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null
      backend_stopped=true
    fi
    rm -f "$BACKEND_PID_FILE"
  fi
  # 兜底：按端口查找并杀掉残留进程
  local port_pids=$(lsof -ti :$BACKEND_PORT 2>/dev/null)
  if [ -n "$port_pids" ]; then
    echo "$port_pids" | xargs kill 2>/dev/null
    sleep 1
    # 强制杀残留
    port_pids=$(lsof -ti :$BACKEND_PORT 2>/dev/null)
    [ -n "$port_pids" ] && echo "$port_pids" | xargs kill -9 2>/dev/null
    backend_stopped=true
  fi
  if $backend_stopped; then
    echo -e "${GREEN}✓ 后端已停止${NC}"
  else
    echo "后端未运行"
  fi

  # 停止前端：先尝试 PID 文件，再按端口兜底
  local frontend_stopped=false
  if [ -f "$FRONTEND_PID_FILE" ]; then
    local pid=$(cat "$FRONTEND_PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null
      sleep 1
      kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null
      frontend_stopped=true
    fi
    rm -f "$FRONTEND_PID_FILE"
  fi
  local port_pids=$(lsof -ti :$FRONTEND_PORT 2>/dev/null)
  if [ -n "$port_pids" ]; then
    echo "$port_pids" | xargs kill 2>/dev/null
    sleep 1
    port_pids=$(lsof -ti :$FRONTEND_PORT 2>/dev/null)
    [ -n "$port_pids" ] && echo "$port_pids" | xargs kill -9 2>/dev/null
    frontend_stopped=true
  fi
  if $frontend_stopped; then
    echo -e "${GREEN}✓ 前端已停止${NC}"
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
