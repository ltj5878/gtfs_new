---
name: gtfs-local-smoke
description: 在 gtfs_new 仓库中启动、排查、验证本地环境时使用。适用于检查 PostgreSQL、后端 5001、前端 5173、start.sh、健康接口、脚本式 API smoke test、日志定位，以及快速判断问题是环境、数据、接口还是页面接入造成的。
---

# GTFS Local Smoke

这个 skill 面向本地联调和快速验收，不是做大改造。

## 默认入口

- 全栈优先使用 `./start.sh start|stop|status|restart`。
- 后端单跑使用 `cd backend && PORT=5001 python3 -m api.app`。
- 前端单跑使用 `cd frontend && npm run dev`。

## 项目约定

- PostgreSQL 16 是默认本地数据库。
- 后端默认端口 `5001`，前端默认端口 `5173`。
- `start.sh` 会把日志写到：
  - `/tmp/gtfs_backend.log`
  - `/tmp/gtfs_frontend.log`
- PID 文件也在 `/tmp`，排查残留进程时先看这些位置。

## 推荐排查顺序

1. 先看 `./start.sh status`，确认 PostgreSQL、后端、前端是否都起来了。
2. 再看 `/api/health`，确认数据库连接不是假启动。
3. 再看基础和业务接口，例如：
   - `/api/stats`
   - `/api/realtime/summary`
   - `/api/punctuality/overview`
4. 如果接口正常但页面异常，再检查前端代理、路由和登录态。
5. 如果页面空白或数据全空，再回头确认是否缺 schema、缺 GTFS 数据或缺 API Key。

## 高价值脚本

- [backend/tests/test_api_quick.py](backend/tests/test_api_quick.py)：适合冒烟确认接口整体没挂。
- [backend/tests/test_punctuality.py](backend/tests/test_punctuality.py)：适合准点率链路改动后检查。
- `check_db.py`、`check_data_detail.py`：适合怀疑 schema 或导入数据异常时使用。

## 常见根因映射

- `health` 失败：数据库、schema 或连接配置问题。
- 后端正常但准点率全空：实时数据、采集服务、准点率表或配置问题。
- 前端能打开但一直跳登录：token、401 处理或路由守卫问题。
- 前端页面接口报错：Axios 路径、region 透传、权限接口或后端返回结构变化。
- 端口占用或假存活：`/tmp` PID 残留或旧进程未退出。

## 输出要求

- 不只说“命令失败”，要说失败落在哪一层。
- 能给出下一步最短验证动作时，优先给动作，不给泛泛建议。
